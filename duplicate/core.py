# -*- coding: utf-8 -*-

from __future__ import absolute_import

from contextlib import closing
from filecmp import cmp
from multiprocessing.pool import ThreadPool
from operator import attrgetter

from .structs import FileInfo, FileGroup, GroupFilter, SkipException
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


def _iterdups(filegrp):
    for key, value in filegrp.dups.items():
        if isinstance(value, FileGroup):
            for subdups, subid, subvalue in _iterdups(value):
                yield subdups, subid, subvalue
        else:
            yield filegrp.dups, key, value


def _itererrors(filegrp):
    yield filegrp.errors

    for key, value in filegrp.dups.items():
        if not isinstance(value, FileGroup):
            continue
        for errlist in _itererrors(value):
            yield errlist


def _cmpfilter(filegrp):
    for dupdict, id, dupfiles in _iterdups(filegrp):

        new_filegrp = FileGroup(filtertype=GroupFilter.Hash)

        if len(dupfiles) == 2:
            try:
                f0, f1 = dupfiles
                if not cmp(f0.path, f1.path, shallow=False):
                    dupdict.pop(id)

            except IOError:
                new_filegrp.errors = dupfiles
                dupdict[id] = new_filegrp

        else:
            for file in dupfiles:
                if file.dev:
                    try:
                        bufsize = _blksizes.setdefault(
                            file.dev, blksize(file.path))
                    except Exception:
                        bufsize = 1
                else:
                    bufsize = None

                try:
                    hash = checksum(file.path, bufsize)
                except Exception:
                    new_filegrp.add_to_errors(file)
                else:
                    new_filegrp.add_to_dups(hash, file)

            new_filegrp.filter()
            dupdict[id] = new_filegrp


def _dupfilter(filegrp, signsize):
    for dupdict, id, dupfiles in _iterdups(filegrp):
        _size = dupfiles[0].size
        if not _size:
            continue

        new_filegrp = FileGroup(filtertype=GroupFilter.Signature)

        signsize = min(_size, signsize)
        for file in dupfiles:
            try:
                sign = signature(file.path, signsize)
            except Exception:
                new_filegrp.add_to_errors(file)
            else:
                new_filegrp.add_to_dups(sign, file)

        new_filegrp.filter()
        dupdict[id] = new_filegrp

        if _size > signsize:
            _cmpfilter(new_filegrp)

    if len(_blksizes) > MAX_BLKSIZES_LEN:
        clear_blkcache()


def _namefilter(filegrp):
    for dupdict, id, dupfiles in _iterdups(filegrp):

        new_filegrp = FileGroup(filtertype=GroupFilter.Name)

        if len(dupfiles) == 2:
            try:
                f0, f1 = dupfiles
                if f0.name != f1.name:
                    dupdict.pop(id)
            except IOError:
                new_filegrp.errors = dupfiles
                dupdict[id] = new_filegrp
        else:
            new_filegrp.filter(dupfiles)
            dupdict[id] = new_filegrp


def _mtimefilter(filegrp):
    for dupdict, id, dupfiles in _iterdups(filegrp):

        new_filegrp = FileGroup(filtertype=GroupFilter.Mtime)

        if len(dupfiles) == 2:
            try:
                f0, f1 = dupfiles
                if f0.mtime != f1.mtime:
                    dupdict.pop(id)
            except IOError:
                new_filegrp.errors = dupfiles
                dupdict[id] = new_filegrp
        else:
            new_filegrp.filter(dupfiles)
            dupdict[id] = new_filegrp


def _permsfilter(filegrp):
    for dupdict, id, dupfiles in _iterdups(filegrp):

        new_filegrp = FileGroup(filtertype=GroupFilter.Mode)

        if len(dupfiles) == 2:
            try:
                f0, f1 = dupfiles
                if f0.mode != f1.mode:
                    dupdict.pop(id)
            except IOError:
                new_filegrp.errors = dupfiles
                dupdict[id] = new_filegrp
        else:
            new_filegrp.filter(dupfiles)
            dupdict[id] = new_filegrp


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
                scanlinks, scanempties, scansystems, scanarchived, scanhidden):

    filegrp = FileGroup(filtertype=GroupFilter.Ident)

    if include:
        included_match = compilecards(include).match
    else:
        def included_match(path):
            return True

    if exclude:
        excluded_match = compilecards(exclude).match
    else:
        def excluded_match(path):
            return False

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
        except (IOError, OSError):
            errnames.append(file)
        else:
            ident = (file.type, file.size)
            filegrp.add_to_dups(ident, file)

    if recursive:
        seen = set()

        def onerror(exception):
            errnames.append(exception.filename)

        for dirname in dirnames:
            dirpath = fullpath(dirname)

            walk_it = _walk(seen, dirpath, onerror, followlinks)
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
                    except (IOError, OSError):
                        errnames.append(file)
                    else:
                        ident = (file.type, file.size)
                        filegrp.add_to_dups(ident, file)

    filegrp.filter()
    unscntuple = splitpaths(errnames, followlinks)

    return filegrp, unscntuple


def _listdups(filegrp):
    with closing(ThreadPool()) as pool:
        dups = [sorted(pool.map(attrgetter('path'), dupfiles))
                for dupdict, id, dupfiles in _iterdups(filegrp) if dupfiles]
    dups.sort(key=len, reverse=True)
    return dups


def _listerrors(filegrp):
    with closing(ThreadPool()) as pool:
        errors = [sorted(pool.map(attrgetter('path'), errlist))
                  for errlist in _itererrors(filegrp) if errlist]
    errors.sort(key=len, reverse=True)
    return errors


def _find(paths,
          minsize=None, include=None, exclude=None,
          comparename=False, comparemtime=False, compareperms=False,
          recursive=True, followlinks=False,
          scanlinks=False, scanempties=False,
          scansystems=True, scanarchived=True, scanhidden=True,
          signsize=None):

    if not paths:
        raise ValueError('Paths must not be empty')

    if minsize is None:
        minsize = DEFAULT_MINSIZE

    if signsize is None:
        signsize = DEFAULT_SIGNSIZE

    filegrp, unscntuple = _filterdups(
        paths, minsize, include, exclude, recursive, followlinks,
        scanlinks, scanempties, scansystems, scanarchived, scanhidden)

    if compareperms:
        _permsfilter(filegrp)

    if comparemtime:
        _mtimefilter(filegrp)

    if comparename:
        _namefilter(filegrp)

    _dupfilter(filegrp, signsize)

    return filegrp, unscntuple


@from_iterable
def find(*paths, **kwargs):
    filegrp, unscntuple = _find(paths, **kwargs)

    dups = _listdups(filegrp)
    errors = _listerrors(filegrp)

    return dups, errors, unscntuple


# @from_iterable
# def fixup():
    # raise NotImplementedError
