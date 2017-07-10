# -*- coding: utf-8 -*-

from __future__ import absolute_import

from contextlib import closing
from filecmp import cmp
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from os.path import isdir, isfile, islink

from .structs import File, SkipException
from .utils import (append_to_dict, blksize, checksum, compilecards, fullpath,
                    fsdecode, signature, _walk)


DEFAULT_HASHTYPE = 'sha1'
DEFAULT_MINSIZE = 100 << 10  #: bytes
DEFAULT_SIGNSIZE = 512  #: bytes

MAX_BLKSIZES_LEN = 128  #: number of cached entries

_BLKSIZES = {}


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


def _hashfilter(dupdict, hashtype):
    for root, key, files in _iterleaves(dupdict):
        newfiles = {}

        for file in files:
            bufsize = _BLKSIZES.setdefault(file.dev, blksize(file.path))
            hash = checksum(file.path, hashtype, bufsize)

            append_to_dict(newfiles, hash, file)

        root[key] = _filterdups(newfiles)


def _dupfilter(dupdict, signsize, hashtype):
    for root, key, files in _iterleaves(dupdict):
        _size = files[0].size
        if not _size:
            continue

        newfiles = {}

        signsize = min(_size, signsize)
        for file in files:
            sign = signature(file.path, signsize)
            append_to_dict(newfiles, sign, file)

        root[key] = _filterdups(newfiles)

        if _size > signsize:
            if len(newfiles) == 2:
                if not cmp(*newfiles, shallow=False):
                    newfiles.pop(key)
            else:
                _hashfilter(newfiles, hashtype)

    if len(_BLKSIZES) > MAX_BLKSIZES_LEN:
        _BLKSIZES.clear()


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


def _splitpaths(paths, followlinks):
    with closing(ThreadPool()) as pool:
        upaths = pool.map(fsdecode, paths)

    dirnames = []
    filenames = []
    linknames = []

    for upath in set(upaths):
        if isdir(upath):
            if not followlinks and islink(upath):
                continue
            dirnames.append(upath)

        elif isfile(upath):
            (linknames if islink(upath) else filenames).append(upath)

    return dirnames, filenames, linknames


def _parsedups(paths, minsize, include, exclude, recursive, followlinks,
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

    dirnames, filenames, linknames = _splitpaths(paths, followlinks)

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

        for dirname in dirnames:
            dirpath = fullpath(dirname)

            for files, links in _walk(seen, dirpath, followlinks):
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

    return _filterdups(dupdict)


def _listdups(dupdict):
    with closing(ThreadPool()) as pool:
        result = [sorted(pool.map(attrgetter('path'), files))
                  for root, key, files in _iterleaves(dupdict)]
    result.sort(key=len, reverse=True)
    return result


def deplicate(paths,
              minsize=None, include=None, exclude=None,
              comparename=False, comparemtime=False, compareperms=False,
              recursive=False, followlinks=False,
              scanlinks=False, scanempties=False,
              scansystems=True, scanarchived=True, scanhidden=True,
              signsize=None, hashtype=None):

    if minsize is None:
        minsize = DEFAULT_MINSIZE

    if signsize is None:
        signsize = DEFAULT_SIGNSIZE

    if hashtype is None:
        hashtype = DEFAULT_HASHTYPE

    dupdict = _parsedups(
        paths, minsize, include, exclude, recursive, followlinks,
        scanlinks, scanempties, scansystems, scanarchived, scanhidden)

    if compareperms:
        _permsfilter(dupdict)

    if comparemtime:
        _mtimefilter(dupdict)

    if comparename:
        _namefilter(dupdict)

    _dupfilter(dupdict, signsize, hashtype)

    return _listdups(dupdict)


# def fixup():
    # raise NotImplementedError
