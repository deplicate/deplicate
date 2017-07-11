# -*- coding: utf-8 -*-

from __future__ import absolute_import

from collections import namedtuple
from enum import IntEnum
from os import lstat
from os.path import basename
from stat import S_IFMT, S_IMODE

from .utils import fullpath


class DupType(IntEnum):
    Ident = 0
    Path = 1
    Name = 2
    Mode = 3
    Ifmt = 4
    Dev = 5
    Mtime = 6
    Size = 7
    Signature = 8
    Hash = 9


class FileDups(object):

    __slots__ = ['type', 'group', 'errors', 'add_to_errors']

    def __init__(self, duptype):
        self.type = duptype
        self.group = {}
        self.errors = []
        self.add_to_errors = self.errors.append

    def add_to_group(self, key, file):
        dups = self.group
        if key in dups:
            dups[key].append(file)
        else:
            dups[key] = [file]

    def _filter(self):
        dupdict = self.group
        for key, value in dupdict.items():
            if isinstance(value, FileDups):
                value._filter()
                value = value.group
            if len(value) < 2:
                dupdict.pop(key)

    def filter(self, files=None):
        for file in files or ():
            self.add_to_group(file[self.type], file)
        self._filter()

    def __str__(self):
        return """FileDups(id={0}, type={1})""".format(id(self), self.type)


_FileInfo = namedtuple('FileInfo', 'ident path name mode ifmt dev mtime size')


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


class SkipException(Exception):
    """
    Skip Exception
    """
    pass
