# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os

from collections import namedtuple
from enum import IntEnum
from operator import attrgetter
from stat import S_IFMT, S_IMODE
from threading import RLock

# from ssd import is_ssd

from .utils.fs import blkdevice, blksize


class SkipException(Exception):
    """
    Skip Exception
    """
    pass


class FilterType(IntEnum):
    ID = 1
    PATH = 2
    NAME = 3
    DIR = 4
    MODE = 5
    IFMT = 6
    DEV = 7
    MTIME = 8
    SIZE = 9
    SIGNATURE = 10
    RULE = 11
    HASH = 12
    BINARY = 13


_counter = 0  # NOTE: No multiprocessing proof.

# NOTE: blkdev is not a unique drive identifier...
_CacheInfo = namedtuple('CacheInfo', 'blkdev blksize')
_DupInfo = namedtuple('DupInfo', 'filter dups errors parent')
_FileInfo = namedtuple('FileInfo',
                       'index id path name dir mode ifmt dev mtime size')
_ResultInfo = namedtuple('ResultInfo',
                         'dups deldups duperrors scanerrors delerrors')


class Cache(object):

    __slots__ = ['__dev', '__info', 'maxlen', 'lock']

    DEFAULT_MAXLEN = 128

    def __init__(self, maxlen=DEFAULT_MAXLEN):
        self.__dev = {}
        self.__info = {}
        self.maxlen = int(maxlen)
        self.lock = RLock()

    def _get(self, blockdevice, path):
        blocksize = blksize(path)
        # ssdflag = is_ssd(path)
        # return _CacheInfo(blockdevice, blocksize, ssdflag)
        return _CacheInfo(blockdevice, blocksize)

    def get(self, fileinfo):
        blockdevice = self.__dev.setdefault(
            fileinfo.dev, blkdevice(fileinfo.path))
        value = self.__info.setdefault(
            blockdevice, self._get(blockdevice, fileinfo.path))
        return value

    def clear(self):
        if self.lock.locked():
            return False
        self.__dev.clear()
        self.__info.clear()
        return True

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()
        if len(self.__dev) > self.maxlen:
            self.clear()


class DupInfo(_DupInfo):

    __slots__ = []

    def __new__(cls, filtertype, dups, errors, parentobj=None, parentkey=None):
        parent = (parentobj, parentkey) if parentobj and parentkey else None

        new = super(DupInfo, cls).__new__
        inst = new(cls, filtertype, dups, errors, parent)

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
            path = os.path.abspath(name)
        if st is None:
            st = os.lstat(name)

        dir, name = os.path.split(name)
        mode = S_IMODE(st.st_mode)
        ifmt = S_IFMT(st.st_mode)
        dev = st.st_dev
        try:
            mtime = st.st_mtime_ns
        except AttributeError:
            mtime = st.st_mtime
        size = st.st_size

        global _counter
        _counter += 1
        keyid = (ifmt, size)

        new = super(FileInfo, cls).__new__
        return new(cls, _counter, keyid, path, name, dir, mode, ifmt, dev,
                   mtime, size)


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
        sort_key = attrgetter('index', 'path')
        dups_it = ResultInfo.__iter_dups(dupinfo)

        dups = [tuple(sorted(duplist, key=sort_key))
                for dupobj, dupkey, duplist in dups_it if duplist]

        dups.sort(key=len, reverse=True)
        return tuple(dups)

    @staticmethod
    def __parse_errors(dupinfo):
        sort_key = attrgetter('index', 'path')
        errors_it = ResultInfo.__iter_errors(dupinfo)

        errors = [tuple(sorted(errlist, key=sort_key))
                  for errlist in errors_it if errlist]

        errors.sort(key=len, reverse=True)
        return tuple(errors)

    def __new__(cls, dupinfo, delduplist, scnerrlist, delerrors):
        dups = cls.__parse_dups(dupinfo)

        deldups = tuple(delduplist)

        duperrors = cls.__parse_errors(dupinfo)
        scanerrors = tuple(scnerrlist)
        delerrors = tuple(delerrors)

        new = super(ResultInfo, cls).__new__
        return new(cls, dups, deldups, duperrors, scanerrors, delerrors)
