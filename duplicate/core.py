# -*- coding: utf-8 -*-

from __future__ import absolute_import

from contextlib import closing
from filecmp import cmp
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from os.path import isdir, isfile, islink

from .structs import File, SkipException
from .utils import (append_to_dict, blksize, checksum, compilecards, fullpath,
                    fsdecode, signature, splitpaths, _walk)


DEFAULT_MINSIZE = 100 << 10  #: bytes
DEFAULT_SIGNSIZE = 512  #: bytes
MAX_BLKSIZES_LEN = 128  #: number of cached entries

_blksizes = {}


def clear_blkcache():
    """
    Clear the blksizes cache.
    """
    _blksizes.clear()


def _filterdups(root):
    for key, value in root.items():
        if isinstance(value, dict):
            root = _filterdups(value)
        elif len(value) < 2:
            root.pop(key)
    return root


def _iterleaves(root):
    for key, value in root.items():
        if isinstance(value, dict):
            for subroot, subkey, subvalue in _iterleaves(value):
                yield subroot, subkey, subvalue
        else:
            yield root, key, value


def _hashfilter(dupdict, errlist):
    for root, key, files in _iterleaves(dupdict):
        newfiles = {}

        for file in files:
            try:
                bufsize = _blksizes.setdefault(file.dev, blksize(file.path))
            except Exception:
                bufsize = 1
            try:
                hash = checksum(file.path, bufsize)
            except Exception:
                errlist.append(file)
            else:
                append_to_dict(newfiles, hash, file)

        root[key] = _filterdups(newfiles)


def _dupfilter(dupdict, errlist, signsize):
    for root, key, files in _iterleaves(dupdict):
        _size = files[0].size
        if not _size:
            continue

        newfiles = {}

        signsize = min(_size, signsize)
        for file in files:
            try:
                sign = signature(file.path, signsize)
            except Exception:
                errlist.append(file)
            else:
                append_to_dict(newfiles, sign, file)

        root[key] = _filterdups(newfiles)

        if _size > signsize:
            if len(newfiles) == 2:
                if not cmp(*newfiles, shallow=False):
                    newfiles.pop(key)
            else:
                _hashfilter(newfiles, errlist)

    if len(_blksizes) > MAX_BLKSIZES_LEN:
        clear_blkcache()


def _namefilter(dupdict):
    for root, key, files in _iterleaves(dupdict):
        if len(files) == 2:
            if files[0].name != files[1].name:
                root.pop(key)
        else:
            newfiles = {}

            for file in files:
                append_to_dict(newfiles, file.name, file)

            root[key] = _filterdups(newfiles)


def _mtimefilter(dupdict):
    for root, key, files in _iterleaves(dupdict):
        if len(files) == 2:
            if files[0].mtime != files[1].mtime:
                root.pop(key)
        else:
            newfiles = {}

            for file in files:
                append_to_dict(newfiles, file.mtime, file)

            root[key] = _filterdups(newfiles)


def _permsfilter(dupdict):
    for root, key, files in _iterleaves(dupdict):
        if len(files) == 2:
            if files[0].mode != files[1].mode:
                root.pop(key)
        else:
            newfiles = {}

            for file in files:
                append_to_dict(newfiles, file.mode, file)

            root[key] = _filterdups(newfiles)


def _filecheck(file, minsize, included_match, excluded_match,
               scanempties, scansystems, scanarchived, scanhidden):
    if not file.size and not scanempties:
        raise SkipException
    elif file.size < minsize:
        raise SkipException

    if excluded_match(file.path):
        raise SkipException
    elif not included_match(file.path):
        raise SkipException

    if not scanhidden and file.is_hidden():
        raise SkipException

    if not scanarchived and file.is_archived():
        raise SkipException

    if not scansystems and file.is_system():
        raise SkipException


def _filterpaths(paths, followlinks):
    with closing(ThreadPool()) as pool:
        upaths = pool.map(fsdecode, paths)

    return splitpaths(set(upaths), followlinks)


def _filterdups(paths, minsize, include, exclude, recursive, followlinks,
               scanlinks, scanempties, scansystems, scanarchived, scanhidden):
    dupdict = {}

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

    if scanlinks:
        filenames += linknames

    for filename in filenames:
        file = File(filename)
        try:
            _filecheck(file, *args)
        except SkipException:
            continue
        id = (file.type, file.size)
        append_to_dict(dupdict, id, file)

    if recursive:
        seen = set()
        errnames = []

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
                    file = File(entry.name, entry.path, st)
                    try:
                        _filecheck(file, *args)
                    except SkipException:
                        continue
                    id = (file.type, file.size)
                    append_to_dict(dupdict, id, file)

    return _filterdups(dupdict), splitpaths(errnames, followlinks)


def _listdups(dupdict):
    with closing(ThreadPool()) as pool:
        result = [sorted(pool.map(attrgetter('path'), files))
                  for root, key, files in _iterleaves(dupdict)]
    result.sort(key=len, reverse=True)
    return result


def _listerrors(errlist):
    with closing(ThreadPool()) as pool:
        return list(pool.map(attrgetter('path'), errlist))


def _find(paths,
         minsize=None, include=None, exclude=None,
         comparename=False, comparemtime=False, compareperms=False,
         recursive=False, followlinks=False,
         scanlinks=False, scanempties=False,
         scansystems=True, scanarchived=True, scanhidden=True,
         signsize=None):

    if minsize is None:
        minsize = DEFAULT_MINSIZE

    if signsize is None:
        signsize = DEFAULT_SIGNSIZE

    errlist = []
    dupdict, unscntuple = _filterdups(
        paths, minsize, include, exclude, recursive, followlinks,
        scanlinks, scanempties, scansystems, scanarchived, scanhidden)

    if compareperms:
        _permsfilter(dupdict)

    if comparemtime:
        _mtimefilter(dupdict)

    if comparename:
        _namefilter(dupdict)

    _dupfilter(dupdict, errlist, signsize)

    return dupdict, errlist, unscntuple


def find(*args, **kwargs):
    dupdict, errlist, unscntuple = _fins(*args, **kwargs)
    return _listdups(dupdict), _listerrors(errlist)


# def fixup():
    # raise NotImplementedError
