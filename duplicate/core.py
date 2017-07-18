# -*- coding: utf-8 -*-

from __future__ import absolute_import

import errno
import os

from contextlib import closing
from filecmp import cmp
from math import ceil
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from os.path import abspath, exists, islink

import xxhash

from .structs import Cache, DupInfo, FileInfo, FilterType, SkipException
from .utils import append_to_dict
from .utils.fs import (blksize, checksum, fsdecode, is_archived, 
                       is_hidden, is_os64, is_system, remove, sidesum, 
                       signature, splitpaths, walk)


_LOWSIZE = 900 if os.name == 'nt' else 60  #: bytes
_MINSIZE = 100 << 10  #: bytes
_BIGSIZE = 100 << 20  #: bytes
_SIZERATE = 10
_BLKSIZE = 4 << 10

_xxhash_xxh = xxhash.xxh64 if is_os64 else xxhash.xxh32

cache = Cache()


def _iterdups(dupinfo):
    for key, value in dupinfo.dups.items():
        if isinstance(value, DupInfo):
            for subobj, subkey, subvalue in _iterdups(value):
                yield subobj, subkey, subvalue
        else:
            yield dupinfo, key, value


def _bufsize(fileinfo):
    # NOTE: stat.st_dev is always zero in Python 2 under Windows. :(
    if fileinfo.dev:
        try:
            value = cache.get(fileinfo).blksize
            
        except Exception:
            value = 1
    else:
        value = blksize(fileinfo.path)
        
    return value


def _checksum(fileinfo):
    try:
        if islink(fileinfo.path):
            link = os.readlink(fileinfo.path)
            hashsum = _xxhash_xxh(link).hexdigest()
        else:
            raise AttributeError

    except AttributeError:
        bufsize = _bufsize(fileinfo)
        hashsum = checksum(fileinfo.path, bufsize)
    return hashsum


def _chksize(fileinfo):
    rate = _SIZERATE
    blksize = _BLKSIZE
    size = int(ceil(fileinfo.size / 100.0 * rate))
    if blksize < size:
        size -= size % blksize
    return size // 2


def _sidesum(fileinfo):
    chunksize = _chksize(fileinfo)
    hashsums = sidesum(fileinfo.path, chunksize)
    return hashsums


def _signature(fileinfo):
    return signature(fileinfo.path)


def _parse(duplist, dupdict, errlist, func, onerror):
    for fileinfo in duplist:
        try:
            idkey = func(fileinfo)

        except SkipException:
            pass

        except (IOError, OSError) as exc:
            onerror(exc, fileinfo.path)

            if exc.errno == errno.ENOENT:
                continue

            errlist.append(fileinfo)

        except Exception as exc:
            onerror(exc, fileinfo.path)

            if not exists(fileinfo.path):
                continue

            errlist.append(fileinfo)

        else:
            append_to_dict(dupdict, idkey, fileinfo)

    return dupdict, errlist


def _rulefilter(dupinfo, onerror, fltrtype, rule, func):
    dups_it = _iterdups(dupinfo)

    for dupobj, dupkey, duplist in dups_it:
        try:
            rule(duplist)

        except SkipException:
            continue

        dupdict, errlist = _parse(duplist, {}, [], func, onerror)
        DupInfo(fltrtype, dupdict, errlist, dupobj, dupkey)


def _binaryfilter(dupinfo, onerror):
    dups_it = _iterdups(dupinfo)

    for dupobj, dupkey, duplist in dups_it:
        try:
            file0, file1 = duplist
        except ValueError:
            continue

        # NOTE: This check can return true one time only; should be optimized?
        if not file0.size:
            continue

        try:
            if cmp(file0.path, file1.path, shallow=False):
                dupdict = {True: duplist}
            else:
                dupdict = {}
            errlist = []

        except (IOError, OSError) as exc:
            onerror(exc, abspath(exc.filename))

            dupdict = {}
            if exc.errno == errno.ENOENT:
                errlist = duplist
            else:
                errlist = []

        DupInfo(FilterType.BINARY, dupdict, errlist, dupobj, dupkey)


def _typefilter(dupinfo, onerror, fltrtype):
    dups_it = _iterdups(dupinfo)

    for dupobj, dupkey, duplist in dups_it:
        dupdict, errlist = _parse(duplist, {}, [], lambda f: f[fltrtype],
                                  onerror)
        DupInfo(fltrtype, dupdict, errlist, dupobj, dupkey)


def _signrule(duplist):
    # if len(duplist) < 2:
        # raise SkipException
    size = duplist[0].size
    path = duplist[0].path
    if not size or _LOWSIZE < size < _MINSIZE:
        raise SkipException
    if islink(path):
        raise SkipException


def _siderule(duplist):
    # if len(duplist) < 2:
        # raise SkipException
    size = duplist[0].size
    path = duplist[0].path
    if size < _BIGSIZE:
        raise SkipException
    if islink(path):
        raise SkipException


def _hashrule(duplist):
    if len(duplist) < 3:
        raise SkipException
    size = duplist[0].size
    if not size:
        raise SkipException


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


def _attrcheck(path, scansystem, scanarchived, scanhidden):
    if not scanhidden and is_hidden(path):
        raise SkipException

    elif not scanarchived and is_archived(path):
        raise SkipException

    elif not scansystem and is_system(path):
        raise SkipException


def _filecheck(fileinfo, minsize, included_match, excluded_match, scanempties,
               scansystem, scanarchived, scanhidden):

    _sizecheck(fileinfo.size, minsize, scanempties)
    _rulecheck(fileinfo.path, included_match, excluded_match)
    _attrcheck(fileinfo.path, scansystem, scanarchived, scanhidden)

    return fileinfo.ifmt, fileinfo.size


def _splitpaths(paths, followlinks):
    with closing(ThreadPool()) as pool:
        upaths = pool.imap(fsdecode, paths)
    return splitpaths(set(upaths), followlinks)


def _names_to_info(names, onerror):
    filelist = []
    scnerrlist = []

    for filename in names:
        try:
            fileinfo = FileInfo(filename)

        except (IOError, OSError) as exc:
            filepath = abspath(filename)

            onerror(exc, filepath)

            if exc.errno == errno.ENOENT:
                continue

            scnerrlist.append(filepath)

        else:
            filelist.append(fileinfo)

    return filelist, scnerrlist


def _entries_to_info(entries, onerror):
    filelist = []
    scnerrlist = []

    for entry in entries:
        try:
            st = entry.stat(follow_symlinks=False)
            fileinfo = FileInfo(entry.name, entry.path, st)

        except (IOError, OSError) as exc:
            filepath = entry.path

            onerror(exc, filepath)

            if exc.errno == errno.ENOENT:
                continue

            scnerrlist.append(filepath)

        else:
            filelist.append(fileinfo)

    return filelist, scnerrlist


def _filescan(filenames, dupdict, errlist, scnerrlist, scnargs, onerror):

    filelist, _scnerrlist = _names_to_info(filenames, onerror)
    scnerrlist.extend(_scnerrlist)

    def check(fileinfo):
        return _filecheck(fileinfo, *scnargs)

    _parse(filelist, dupdict, errlist, check, onerror)

    return dupdict, errlist, scnerrlist


def _dirscan(dirnames, dupdict, errlist, scnerrlist,
             scnargs, onerror, followlinks, scanlinks):

    def callback(exc):
        filepath = abspath(exc.filename)
        onerror(exc, filepath)
        scnerrlist.append(filepath)

    def check(fileinfo):
        return _filecheck(fileinfo, *scnargs)

    seen = set()
    for dirname in dirnames:
        walk_it = walk(dirname, callback, followlinks, seen)

        for dirs, files, links in walk_it:
            if scanlinks:
                files += links

            filelist, _scnerrlist = _entries_to_info(files, onerror)
            scnerrlist.extend(_scnerrlist)

            _parse(filelist, dupdict, errlist, check, onerror)

    return dupdict, errlist, scnerrlist


def filterdups(fltrtype, dupinfo, onerror):

    if fltrtype is FilterType.SIGNATURE:
        _rulefilter(dupinfo, onerror, fltrtype, _signrule, _signature)

    elif fltrtype is FilterType.RULE:
        # NOTE: Just a one-pass sidesum check for now...
        _rulefilter(dupinfo, onerror, fltrtype, _siderule, _sidesum)

    elif fltrtype is FilterType.HASH:
        _rulefilter(dupinfo, onerror, fltrtype, _hashrule, _checksum)

    elif fltrtype is FilterType.BINARY:
        _binaryfilter(dupinfo, onerror)

    else:
        _typefilter(dupinfo, onerror, fltrtype)

    return dupinfo


def purgedups(dupinfo, trash, ondel, onerror):
    delduplist = []
    delerrlist = []

    sort_key = attrgetter('index', 'path')
    dups_it = _iterdups(dupinfo)

    for dupobj, dupkey, duplist in dups_it:

        duplicates = sorted(duplist, key=sort_key)[1:]

        for fileinfo in duplicates:
            filepath = fileinfo.path

            try:
                ondel(filepath)
            except SkipException:
                continue

            try:
                remove(filepath, trash)

            except (IOError, OSError) as exc:
                onerror(exc, filepath)

                if exc.errno == errno.ENOENT:
                    continue

                delerrlist.append(filepath)

            except Exception as exc:
                onerror(exc, filepath)

                if not exists(filepath):
                    continue

                delerrlist.append(filepath)

            else:
                delduplist.append(filepath)

    return delduplist, delerrlist


def scandups(paths, minsize, matchers, recursive, followlinks, scanlinks,
             flags, onerror):

    dupdict = {}
    errlist = []
    scnerrlist = []

    scnargs = (minsize,) + matchers + flags

    splitted_paths = _splitpaths(paths, followlinks)
    dirnames, filenames, linknames, _, errnames = splitted_paths

    scnerrlist.extend(errnames)

    if scanlinks:
        filenames += linknames

    _filescan(filenames, dupdict, errlist, scnerrlist, scnargs, onerror)

    if recursive:
        _dirscan(dirnames, dupdict, errlist, scnerrlist, scnargs, onerror,
                 followlinks, scanlinks)

    dupinfo = DupInfo(FilterType.ID, dupdict, errlist)

    return dupinfo, scnerrlist
