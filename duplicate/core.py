# -*- coding: utf-8 -*-

from __future__ import absolute_import

from contextlib import closing
from filecmp import cmp
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from os.path import exists

from .structs import DupType, FileDups, FileInfo, SkipException
from .utils import (_walk, blksize, checksum, compilecards, from_iterable,
                    fsdecode, fullpath, is_archived, is_hidden, is_system,
                    signature, splitpaths)

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


def _hashbufsize(file):
    if file.dev:
        try:
            bufsize = _blksizes.setdefault(file.dev, blksize(file.path))
        except Exception:
            bufsize = 1
    else:
        bufsize = None

    return bufsize


def _hashhandler(new_filedups, dupfiles, onerror):
    for file in dupfiles:
        path = file.path
        try:
            bufsize = _hashbufsize(file)
            hashsum = checksum(path, bufsize)

        except Exception as exc:
            onerror(path, exc)
            if exists(path):
                new_filedups.add_to_errors(file)

        else:
            new_filedups.add_to_group(hashsum, file)


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
            _hashhandler(new_filedups, dupfiles, onerror)

            new_filedups.filter()
            dupdict[dupkey] = new_filedups


def _signhandler(new_filedups, dupfiles, signsize, onerror):
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


def _hashfilter(filedups, signsize, onerror):
    for dupdict, dupkey, dupfiles in _iterdups(filedups):
        _size = dupfiles[0].size
        if not _size:
            continue

        new_filedups = FileDups(DupType.Signature)

        signsize = min(_size, signsize)
        _signhandler(new_filedups, dupfiles, signsize, onerror)

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


def _sizecheck(size, minsize, scanempties):
    if not size and not scanempties:
        raise SkipException

    elif size < minsize:
        raise SkipException


def _rulecheck(path, included_match, excluded_match):
    if excluded_match(path):
        raise SkipException

    elif not included_match(path):
        raise SkipException


def _attrcheck(path, scansystems, scanarchived, scanhidden):
    if not scanhidden and is_hidden(path):
        raise SkipException

    elif not scanarchived and is_archived(path):
        raise SkipException

    elif not scansystems and is_system(path):
        raise SkipException


def _filecheck(file, minsize, included_match, excluded_match,
               scanempties, scansystems, scanarchived, scanhidden):

    _sizecheck(file.size, minsize, scanempties)
    _rulecheck(file.path, included_match, excluded_match)
    _attrcheck(file.path, scansystems, scanarchived, scanhidden)


def _filterpaths(paths, followlinks):
    with closing(ThreadPool()) as pool:
        upaths = pool.map(fsdecode, paths)

    return splitpaths(set(upaths), followlinks)


def _filehandler(filedups, errnames, filename, filepath, filestat, args,
                 onerror):
    file = FileInfo(filename, filepath, filestat)
    try:
        _filecheck(file, *args)

    except SkipException:
        pass

    except (IOError, OSError) as exc:
        path = file.path
        onerror(path, exc)
        if exists(path):
            errnames.append(path)

    else:
        ident = (file.ifmt, file.size)
        filedups.add_to_group(ident, file)


def _filescanner(filedups, filenames, args, onerror):
    errnames = []

    for filename in filenames:
        _filehandler(filedups, errnames, filename, None, None, args, onerror)

    return errnames


def _dirscanner(filedups, dirnames, args, followlinks, scanlinks, onerror):
    errnames = []
    seen = set()

    def callback(exc):
        onerror(exc.filename, exc)
        errnames.append(exc.filename)

    for dirname in dirnames:
        walk_it = _walk(seen, fullpath(dirname), callback, followlinks)

        for files, links in walk_it:
            if scanlinks:
                files += links

            for entry in files:
                st = entry.stat(follow_symlinks=False)
                _filehandler(filedups, errnames, entry.name, entry.path, st,
                             args, onerror)

    return errnames


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

    if scanlinks:
        filenames += linknames

    errnames = _filescanner(filedups, filenames, args, onerror)

    if recursive:
        errnames.extend(
            _dirscanner(filedups, dirnames, args, followlinks, scanlinks,
                        onerror))

    filedups.filter()

    return filedups, errnames


def _listdups(filedups):
    with closing(ThreadPool()) as pool:
        dups = [sorted(pool.map(attrgetter('path'), dupfiles))
                for dupdict, dupkey, dupfiles in _iterdups(filedups)
                if dupfiles]
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
          signsize=None, onerror=None, notify=lambda s, p=None: None):

    notify('preparing to scan')

    if not paths:
        raise ValueError('Paths must not be empty')

    if minsize is None:
        minsize = DEFAULT_MINSIZE

    if signsize is None:
        signsize = DEFAULT_SIGNSIZE

    notify('scanning for similar files')

    filedups, scanerrors = _filterdups(
        paths, minsize, include, exclude, recursive, followlinks,
        scanlinks, scanempties, scansystems, scanarchived, scanhidden,
        onerror)

    if compareperms:
        notify('filtering files by permission mode')
        _filter(DupType.Mode, filedups)

    if comparemtime:
        notify('filtering files by modification time')
        _filter(DupType.Mtime, filedups)

    if comparename:
        notify('filtering files by name')
        _filter(DupType.Name, filedups)

    notify('filtering files by content')
    _hashfilter(filedups, signsize, onerror or (lambda f, e: None))

    notify('finalizing results')
    return filedups, scanerrors


@from_iterable
def find(*paths, **kwargs):
    filedups, scanerrors = _find(paths, **kwargs)

    kwargs.pop('notify', None)

    dups = _listdups(filedups)
    errors = _listerrors(filedups)

    return dups, errors, scanerrors


# @from_iterable
# def purge():
    # raise NotImplementedError
