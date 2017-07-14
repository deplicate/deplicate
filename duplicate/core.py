# -*- coding: utf-8 -*-

from __future__ import absolute_import

from contextlib import closing
from filecmp import cmp
from math import ceil
from multiprocessing.pool import ThreadPool
from os.path import exists

from .structs import (Cache, DupInfo, FileInfo, FilterType, LogLevel,
                      ResultInfo, SkipException)
from .utils import (SIDESUM_PERCENT, SIGNATURE_SIZE, append_to_dict, blksize,
                    checksum, compilecards, from_iterable, fsdecode, fullpath,
                    is_archived, is_hidden, is_system, sidesum, signature,
                    splitpaths, walk)

DEFAULT_MINSIZE = 100 << 10  #: bytes

_cache = Cache()


def clear_cache():
    """
    Clear the internal cache.
    """
    _cache.clear()


def _iterdups(dupinfo):
    for key, value in dupinfo.dups.items():
        if isinstance(value, DupInfo):
            for subobj, subkey, subvalue in _iterdups(value):
                yield subobj, subkey, subvalue
        else:
            yield dupinfo, key, value


def _blksize(fileinfo):
    # NOTE: stat.st_dev is always zero in Python 2 under Windows. :(
    if fileinfo.dev:
        try:
            value = _cache.get(fileinfo).blksize
        except Exception:
            value = 1
    else:
        value = blksize(fileinfo.name)

    return value


def _checksum(fileinfo):
    bufsize = _blksize(fileinfo)
    hashsum = checksum(fileinfo.path, bufsize)
    return hashsum


def _signature(fileinfo):
    return hash(signature(fileinfo.path))


def _sidesize(fileinfo):
    percsize = int(ceil(fileinfo.size / 100.0 * SIDESUM_PERCENT))
    blocksize = _blksize(fileinfo)
    if blocksize < percsize:
        percsize -= percsize % blocksize
    return percsize // 2


def _sidesum(fileinfo):
    return sidesum(fileinfo.path, _sidesize(fileinfo))


def _parse(duplist, func, onerror, dupdict=None, errlist=None):
    if dupdict is None:
        dupdict = {}
    if errlist is None:
        errlist = []

    for fileinfo in duplist:
        try:
            id = func(fileinfo)

        except SkipException:
            pass

        except Exception as exc:
            if onerror is not None:
                onerror(exc, fileinfo.path)
            if not exists(fileinfo.path):
                continue
            errlist.append(fileinfo)

        else:
            append_to_dict(dupdict, id, fileinfo)

    return dupdict, errlist


def _hashfilter(filtertype, dupinfo, onerror):
    if filtertype is FilterType.HASH:
        func = _checksum
        minsize = SIGNATURE_SIZE + 1
        minlen = 3

    elif filtertype is FilterType.RULE:
        func = _sidesum
        minsize = SIGNATURE_SIZE + 1
        minlen = 2

    else:
        func = _signature
        minsize = 1
        minlen = 2

    for dupobj, dupkey, duplist in _iterdups(dupinfo):
        if len(duplist) < minlen:
            continue

        # NOTE: This check can return true one time only; should be optimized?
        if duplist[0].size < minsize:
            continue

        dupdict, errlist = _parse(duplist, func, onerror)
        DupInfo(filtertype, dupdict, errlist, dupobj, dupkey)


def _binaryfilter(filtertype, dupinfo, onerror):
    for dupobj, dupkey, duplist in _iterdups(dupinfo):
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

        except IOError as exc:
            if onerror is not None:
                onerror(exc, exc.filename)

            dupdict = {}
            if exists(file0.path) and exists(file1.path):
                errlist = duplist
            else:
                errlist = []

        DupInfo(filtertype, dupdict, errlist, dupobj, dupkey)


def _stfilter(filtertype, dupinfo, onerror):
    for dupobj, dupkey, duplist in _iterdups(dupinfo):
        dupdict, errlist = _parse(duplist, lambda f: f[filtertype], onerror)
        DupInfo(filtertype, dupdict, errlist, dupobj, dupkey)


def _filter(filtertype, dupinfo, onerror):
    if filtertype is FilterType.BINARY:
        _binaryfilter(filtertype, dupinfo, onerror)

    elif filtertype in (FilterType.HASH, FilterType.RULE,
                        FilterType.SIGNATURE):
        _hashfilter(filtertype, dupinfo, onerror)

    else:
        _stfilter(filtertype, dupinfo, onerror)


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

        except IOError as exc:
            if onerror is not None:
                onerror(exc, filename)
            if not exists(filename):
                continue
            scnerrlist.append(filename)

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

        except IOError as exc:
            if onerror is not None:
                onerror(exc, entry.path)
            if not exists(entry.path):
                continue
            scnerrlist.append(entry.path)

        else:
            filelist.append(fileinfo)

    return filelist, scnerrlist


def _filescan(filenames, args, onerror,
              dupdict=None, errlist=None, scnerrlist=None):

    if dupdict is None:
        dupdict = {}
    if errlist is None:
        errlist = []
    if scnerrlist is None:
        scnerrlist = []

    filelist, _scnerrlist = _names_to_info(filenames, onerror)
    scnerrlist.extend(_scnerrlist)

    def check(fileinfo):
        return _filecheck(fileinfo, *args)

    _parse(filelist, check, onerror, dupdict, errlist)

    return dupdict, errlist, scnerrlist


def _dirscan(dirnames, args, onerror, followlinks, scanlinks,
             dupdict=None, errlist=None, scnerrlist=None):
    seen = set()

    if dupdict is None:
        dupdict = {}
    if errlist is None:
        errlist = []
    if scnerrlist is None:
        scnerrlist = []

    if onerror is not None:
        def callback(exc):
            onerror(exc, exc.filename)
            scnerrlist.append(exc.filename)
    else:
        def callback(exc):
            scnerrlist.append(exc.filename)

    def check(fileinfo):
        return _filecheck(fileinfo, *args)

    for dirname in dirnames:
        walk_it = walk(dirname, callback, followlinks, seen)

        for dirs, files, links in walk_it:
            if scanlinks:
                files += links

            filelist, _scnerrlist = _entries_to_info(files, onerror)
            scnerrlist.extend(_scnerrlist)

            _parse(filelist, check, onerror, dupdict, errlist)

    return dupdict, errlist, scnerrlist


def _filterdups(paths, minsize, include, exclude, recursive, followlinks,
                scanlinks, scanempties, scansystem, scanarchived, scanhidden,
                onerror):

    cc = compilecards
    included_match = cc(include).match if include else lambda p: True
    excluded_match = cc(exclude).match if exclude else lambda p: False

    args = (minsize, included_match, excluded_match, scanempties, scansystem,
            scanarchived, scanhidden)

    dirnames, filenames, linknames = _splitpaths(paths, followlinks)

    if scanlinks:
        filenames += linknames

    dupdict, errlist, scnerrlist = _filescan(filenames, args, onerror)

    if recursive:
        _dirscan(dirnames, args, onerror, followlinks, scanlinks,
                 dupdict, errlist, scnerrlist)

    dupinfo = DupInfo(FilterType.ID, dupdict, errlist)

    return dupinfo, scnerrlist


def _cpuprocess(dupinfo, comparename, comparemtime, comparemode, onerror,
                notify):
    if comparemode:
        notify('filtering files by permission mode')
        _filter(FilterType.MODE, dupinfo, onerror)

    if comparemtime:
        notify('filtering files by modification time')
        _filter(FilterType.MTIME, dupinfo, onerror)

    if comparename:
        notify('filtering files by name')
        _filter(FilterType.NAME, dupinfo, onerror)


def _ioprocess(dupinfo, onerror, notify):
    notify('filtering files by signature')
    _filter(FilterType.SIGNATURE, dupinfo, onerror)

    notify('filtering files by rule')
    if SIDESUM_PERCENT < 100:
        _filter(FilterType.RULE, dupinfo, onerror)
    else:
        notify('skipped rule filtering', LogLevel.WARNING)

    notify('filtering files by hash')
    _filter(FilterType.HASH, dupinfo, onerror)

    notify('filtering files by content')
    _filter(FilterType.BINARY, dupinfo, onerror)

    _cache.optimize()


def _process(dupinfo, kwgs):
    notify = kwgs['notify']
    notify('preparing to process')

    comparename = kwgs['comparename']
    comparemtime = kwgs['comparemtime']
    comparemode = kwgs['comparemode']
    onerror = kwgs['onerror']

    _cpuprocess(dupinfo, comparename, comparemtime, comparemode, onerror,
                notify)
    _ioprocess(dupinfo, onerror, notify)


def _scan(paths, kwgs):
    notify = kwgs['notify']
    notify('preparing to scan')

    minsize = kwgs['minsize']
    include = kwgs['include']
    exclude = kwgs['exclude']
    recursive = kwgs['recursive']
    followlinks = kwgs['followlinks']
    scanlinks = kwgs['scanlinks']
    scanempties = kwgs['scanempties']
    scansystem = kwgs['scansystem']
    scanarchived = kwgs['scanarchived']
    scanhidden = kwgs['scanhidden']
    onerror = kwgs['onerror']

    notify('scanning for similar files')
    dupinfo, scnerrlist = _filterdups(
        paths, minsize, include, exclude, recursive, followlinks, scanlinks,
        scanempties, scansystem, scanarchived, scanhidden, onerror)

    return dupinfo, scnerrlist


def _notify(text, level=LogLevel.INFO, progress=None):
    pass


def _find(paths, minsize=DEFAULT_MINSIZE, include=None, exclude=None,
          comparename=False, comparemtime=False, comparemode=False,
          recursive=True, followlinks=False,
          scanlinks=False, scanempties=False,
          scansystem=True, scanarchived=True, scanhidden=True,
          onerror=None, notify=_notify):

    if not paths:
        raise ValueError('Paths must not be empty')

    kwgs = locals()
    kwgs.pop('paths')

    dupinfo, scnerrlist = _scan(paths, kwgs)

    _process(dupinfo, kwgs)

    notify('finalizing results')
    return dupinfo, scnerrlist


@from_iterable
def find(*paths, **kwargs):
    dupinfo, scnerrlist = _find(paths, **kwargs)
    return ResultInfo(dupinfo, scnerrlist)


# @from_iterable
# def purge(*paths, **kwargs):
    # trash = kwargs.pop('trash', True)
    # ondel = kwargs.pop('trash', None)

    # dupinfo, scnerrlist = _find(paths, **kwargs)

    # raise NotImplementedError
