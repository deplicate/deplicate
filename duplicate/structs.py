# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from collections import namedtuple
from contextlib import closing
from enum import IntEnum
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from os import lstat
from os.path import basename
from stat import S_IFMT, S_IMODE

from .utils import blkdevice, blksize, fullpath, is_ssd


class SkipException(Exception):
    """
    Skip Exception
    """
    pass


class FilterType(IntEnum):
    ID = 0
    PATH = 1
    NAME = 2
    MODE = 3
    IFMT = 4
    DEV = 5
    MTIME = 6
    SIZE = 7
    SIGNATURE = 8
    RULE = 9
    HASH = 10
    BINARY = 11


class LogLevel(IntEnum):
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


# NOTE: blkdev is not a unique drive identifier...
_CacheInfo = namedtuple('CacheInfo', 'blkdev blksize ssd')
_DupInfo = namedtuple('DupInfo', 'filter dups errors parent')
_FileInfo = namedtuple('FileInfo', 'ident path name mode ifmt dev mtime size')
_ResultInfo = namedtuple('ResultInfo', 'dups duperrors scanerrors')


class Cache(object):

    __slots__ = ['__dev', '__info']

    MAX_LEN = 128  #: number of cached entries

    def __init__(self):
        self.__dev = {}
        self.__info = {}

    def _get(self, blockdev, path):
        blocksize = blksize(path)
        ssdflag = is_ssd(path)
        return _CacheInfo(blockdev, blocksize, ssdflag)

    def get(self, fileinfo):
        blockdev = self.__dev.setdefault(fileinfo.dev,
                                         blkdevice(fileinfo.path))
        value = self.__info.setdefault(blockdev,
                                       self._get(blockdev, fileinfo.path))
        return value

    def clear(self):
        self.__dev.clear()
        self.__info.clear()

    def optimize(self):
        if len(self.__dev) > self.MAX_LEN:
            self.clear()


class DupInfo(_DupInfo):

    __slots__ = []

    def __new__(cls, filtertype, dups, errors, parentobj=None, parentkey=None):
        parent = (parentobj, parentkey) if parentobj and parentkey else None

        inst = super(DupInfo, cls).__new__(
            cls, filtertype, dups, errors, parent)

        if parent:
            parentobj.dups[parentkey] = inst

        return inst

    def __init__(self, *args, **kwargs):
        super(DupInfo, self).__init__(*args, **kwargs)
        self._filter()

    def _filter(self, key=None):
        dupdict = self.dups

        if key is None:
            for key, value in dupdict.items():
                if len(value) > 1:
                    continue
                dupdict.pop(key)
        else:
            dupdict.pop(key, None)

        if not dupdict and not self.errors and self.parent:
            parentobj, parentkey = self.parent
            parentobj._filter(parentkey)


class FileInfo(_FileInfo):

    __slots__ = []

    def __new__(cls, name, path=None, st=None):
        if path is None:
            path = fullpath(name)
        if st is None:
            st = lstat(name)

        name = basename(name)
        mode = S_IMODE(st.st_mode)
        ifmt = S_IFMT(st.st_mode)
        dev = st.st_dev
        try:
            mtime = st.st_mtime_ns
        except AttributeError:
            mtime = st.st_mtime
        size = st.st_size
        ident = (ifmt, size)

        return super(FileInfo, cls).__new__(
            cls, ident, path, name, mode, ifmt, dev, mtime, size)


class ResultInfo(_ResultInfo):

    __slots__ = []

    @staticmethod
    def __iter_dups(dupinfo):
        for key, value in dupinfo.dups.items():
            if isinstance(value, DupInfo):
                dups_it = ResultInfo.__iter_dups(value)
                for subobj, subkey, subvalue in dups_it:
                    yield subobj, subkey, subvalue
            else:
                yield dupinfo, key, value

    @staticmethod
    def __iter_errors(dupinfo):
        yield dupinfo.errors

        for value in dupinfo.dups.values():
            if not isinstance(value, DupInfo):
                continue
            for errlist in ResultInfo.__iter_errors(value):
                yield errlist

    @staticmethod
    def __parse_dups(dupinfo):
        filter_fn = attrgetter('path')
        dups_it = ResultInfo.__iter_dups(dupinfo)

        with closing(ThreadPool()) as pool:
            dups = [tuple(sorted(pool.imap_unordered(filter_fn, duplist)))
                    for dupobj, dupkey, duplist in dups_it if duplist]

        dups.sort(key=len, reverse=True)
        return tuple(dups)

    @staticmethod
    def __parse_errors(dupinfo):
        filter_fn = attrgetter('path')
        errors_it = ResultInfo.__iter_errors(dupinfo)

        with closing(ThreadPool()) as pool:
            errors = [sorted(pool.imap_unordered(filter_fn, errlist))
                      for errlist in errors_it if errlist]

        errors.sort(key=len, reverse=True)
        return tuple(errors)

    def __new__(cls, dupinfo, scnerrlist):
        dups = cls.__parse_dups(dupinfo)
        duperrors = cls.__parse_errors(dupinfo)
        scanerrors = tuple(scnerrlist)
        return super(ResultInfo, cls).__new__(cls, dups, duperrors, scanerrors)
