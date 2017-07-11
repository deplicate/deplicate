# -*- coding: utf-8 -*-

from __future__ import absolute_import

from contextlib import closing
from filecmp import cmp
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from os.path import exists

from .structs import FileInfo, FileDups, DupType, SkipException
from .utils import (blksize, checksum, compilecards, from_iterable, fullpath,
                    fsdecode, is_archived, is_hidden, is_system, signature,
                    splitpaths, _walk)


DEFAULT_MINSIZE = 100 << 10  #: bytes
DEFAULT_SIGNSIZE = 512  #: bytes
MAX_BLKSIZES_LEN = 128  #: number of cached entries

_blksizes = {}


def clear_blkcache():
    """
    Clear the blksizes cache.
    """
    _blksizes.clear()


def _iterdups(filedups):
    for key, value in filedups.group.items():
        if isinstance(value, FileDups):
            for subgroup, subkey, subvalue in _iterdups(value):
                yield subgroup, subkey, subvalue
        else:
            yield filedups.group, key, value


def _itererrors(filedups):
    yield filedups.errors

    for value in filedups.group.values():
        if not isinstance(value, FileDups):
            continue
        for errlist in _itererrors(value):
            yield errlist


def _binaryfilter(filedups, onerror):
    for dupdict, dupkey, dupfiles in _iterdups(filedups):

        new_filedups = FileDups(DupType.Hash)

        if len(dupfiles) == 2:
            try:
                f0, f1 = dupfiles
                if not cmp(f0.path, f1.path, shallow=False):
                    dupdict.pop(dupkey)

            except IOError:
                new_filedups.errors = dupfiles
                dupdict[dupkey] = new_filedups

        else:
            for file in dupfiles:
                path = file.path

                if file.dev:
                    try:
                        bufsize = _blksizes.setdefault(
                            file.dev, blksize(path))
                    except Exception:
                        bufsize = 1
                else:
                    bufsize = None

                try:
                    hashsum = checksum(path, bufsize)

                except Exception as exc:
                    onerror(path, exc)
                    if exists(path):
                        new_filedups.add_to_errors(file)

                else:
                    new_filedups.add_to_group(hashsum, file)

            new_filedups.filter()
            dupdict[dupkey] = new_filedups


def _hashfilter(filedups, signsize, onerror):
    for dupdict, dupkey, dupfiles in _iterdups(filedups):
        _size = dupfiles[0].size
        if not _size:
            continue

        new_filedups = FileDups(DupType.Signature)

        signsize = min(_size, signsize)
        for file in dupfiles:
            path = file.path
            try:
                sign = signature(path, signsize)

            except Exception as exc:
                onerror(path, exc)
                if exists(path):
                    new_filedups.add_to_errors(file)

            else:
                new_filedups.add_to_group(sign, file)

        new_filedups.filter()
        dupdict[dupkey] = new_filedups

        if _size > signsize:
            _binaryfilter(new_filedups, onerror)

    if len(_blksizes) > MAX_BLKSIZES_LEN:
        clear_blkcache()


def _filter(duptype, filedups):
    for dupdict, dupkey, dupfiles in _iterdups(filedups):

        new_filedups = FileDups(duptype)

        if len(dupfiles) == 2:
            try:
                f0, f1 = dupfiles
                if f0[duptype] != f1[duptype]:
                    dupdict.pop(dupkey)
            except IOError:
                new_filedups.errors = dupfiles
                dupdict[dupkey] = new_filedups
        else:
            new_filedups.filter(dupfiles)
            dupdict[dupkey] = new_filedups


def _namefilter(filedups):
    return _filter(DupType.Name, filedups)


def _mtimefilter(filedups):
    return _filter(DupType.Mtime, filedups)


def _permsfilter(filedups):
    return _filter(DupType.Mode, filedups)


def _filecheck(file, minsize, included_match, excluded_match,
               scanempties, scansystems, scanarchived, scanhidden):

    path = file.path
    size = file.size

    if not size and not scanempties:
        raise SkipException
    elif size < minsize:
        raise SkipException

    if excluded_match(path):
        raise SkipException
    elif not included_match(path):
        raise SkipException

    if not scanhidden and is_hidden(path):
        raise SkipException

    if not scanarchived and is_archived(path):
        raise SkipException

    if not scansystems and is_system(path):
        raise SkipException


def _filterpaths(paths, followlinks):
    with closing(ThreadPool()) as pool:
        upaths = pool.map(fsdecode, paths)

    return splitpaths(set(upaths), followlinks)


def _filterdups(paths, minsize, include, exclude, recursive, followlinks,
                scanlinks, scanempties, scansystems, scanarchived, scanhidden,
                onerror):

    filedups = FileDups(DupType.Ident)

    cc = compilecards
    included_match = cc(include).match if include else lambda p: True
    excluded_match = cc(exclude).match if exclude else lambda p: False

    args = (minsize, included_match, excluded_match, scanempties, scansystems,
            scanarchived, scanhidden)

    dirnames, filenames, linknames = _filterpaths(paths, followlinks)
    errnames = []

    if scanlinks:
        filenames += linknames

    for filename in filenames:
        file = FileInfo(filename)
        try:
            _filecheck(file, *args)

        except SkipException:
            continue

        except (IOError, OSError) as exc:
            path = file.path
            onerror(path, exc)
            if exists(path):
                errnames.append(path)

        else:
            ident = (file.ifmt, file.size)
            filedups.add_to_group(ident, file)

    if recursive:
        seen = set()

        def _onerror(exc):
            onerror(exc.filename, exc)
            errnames.append(exc.filename)

        for dirname in dirnames:
            dirpath = fullpath(dirname)

            walk_it = _walk(seen, dirpath, _onerror, followlinks)

            for files, links in walk_it:
                if scanlinks:
                    files += links

                for entry in files:
                    st = entry.stat(follow_symlinks=False)
                    file = FileInfo(entry.name, entry.path, st)
                    try:
                        _filecheck(file, *args)

                    except SkipException:
                        continue

                    except (IOError, OSError) as exc:
                        path = file.path
                        onerror(path, exc)
                        if exists(path):
                            errnames.append(path)

                    else:
                        ident = (file.ifmt, file.size)
                        filedups.add_to_group(ident, file)

    filedups.filter()

    return filedups, errnames


def _listdups(filedups):
    with closing(ThreadPool()) as pool:
        dups = [sorted(pool.map(attrgetter('path'), dupfiles))
                for dupdict, dupkey, dupfiles in _iterdups(filedups) if dupfiles]
    dups.sort(key=len, reverse=True)
    return dups


def _listerrors(filedups):
    with closing(ThreadPool()) as pool:
        errors = [sorted(pool.map(attrgetter('path'), errlist))
                  for errlist in _itererrors(filedups) if errlist]
    errors.sort(key=len, reverse=True)
    return errors


def _find(paths,
          minsize=None, include=None, exclude=None,
          comparename=False, comparemtime=False, compareperms=False,
          recursive=True, followlinks=False,
          scanlinks=False, scanempties=False,
          scansystems=True, scanarchived=True, scanhidden=True,
          signsize=None, onerror=None):

    if not paths:
        raise ValueError('Paths must not be empty')

    if minsize is None:
        minsize = DEFAULT_MINSIZE

    if signsize is None:
        signsize = DEFAULT_SIGNSIZE

    filedups, scanerrors = _filterdups(
        paths, minsize, include, exclude, recursive, followlinks,
        scanlinks, scanempties, scansystems, scanarchived, scanhidden,
        onerror)

    if compareperms:
        _permsfilter(filedups)

    if comparemtime:
        _mtimefilter(filedups)

    if comparename:
        _namefilter(filedups)

    _hashfilter(filedups, signsize, onerror or (lambda f, e: None))

    return filedups, scanerrors


@from_iterable
def find(*paths, **kwargs):
    filedups, scanerrors = _find(paths, **kwargs)

    dups = _listdups(filedups)
    errors = _listerrors(filedups)

    return dups, errors, scanerrors


# @from_iterable
# def fixup():
    # raise NotImplementedError
