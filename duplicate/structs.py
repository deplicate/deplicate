# -*- coding: utf-8 -*-

from __future__ import absolute_import

from collections import namedtuple
from enum import IntEnum
from os import lstat
from os.path import basename
from stat import S_IFMT, S_IMODE

from .utils import fullpath


class GroupFilter(IntEnum):
    Ident = 0
    Path = 1
    Name = 2
    Mode = 3
    Type = 4
    Dev = 5
    Mtime = 6
    Size = 7
    Signature = 8
    Hash = 9


class FileGroup(object):

    __slots__ = ['id', 'type', 'dups', 'errors', 'add_to_errors']

    def __init__(self, filtertype):
        self.id = id(self)
        self.type = filtertype
        self.dups = {}
        self.errors = []
        self.add_to_errors = self.errors.append

    def add_to_dups(self, id, file):
        dups = self.dups
        if id in dups:
            dups[id].append(file)
        else:
            dups[id] = [file]

    def _filter(self):
        dupdict = self.dups
        for key, value in dupdict.items():
            if isinstance(value, FileGroup):
                value._filter()
                value = value.dups
            if len(value) < 2:
                dupdict.pop(key)

    def filter(self, files=None):
        if files:
            for file in files:
                self.add_to_dups(file[self.type], file)
        self._filter()

    def __str__(self):
        return """FileGroup(id={0}, type={1})""".format(self.id, self.type)


_FileInfo = namedtuple('FileInfo', 'ident path name mode type dev mtime size')


class FileInfo(_FileInfo):

    __slots__ = []

    def __new__(cls, name, path=None, st=None):
        if path is None:
            path = fullpath(name)
        if st is None:
            st = lstat(name)

        name = basename(name)
        mode = S_IMODE(st.st_mode)
        type = S_IFMT(st.st_mode)
        dev = st.st_dev
        try:
            mtime = st.st_mtime_ns
        except AttributeError:
            mtime = st.st_mtime
        size = st.st_size
        ident = (type, size)

        return super(FileInfo, cls).__new__(
            cls, ident, path, name, mode, type, dev, mtime, size)


class SkipException(Exception):
    """
    Skip Exception
    """
    pass
