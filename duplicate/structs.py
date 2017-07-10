# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os import lstat
from os.path import basename
from stat import S_IFMT, S_IMODE

from .utils import fullpath, is_archived, is_hidden, is_system


class File(object):

    __slots__ = ['_archived', '_hidden', '_system',
                 'name', 'path', 'mode', 'type', 'dev', 'size', 'mtime']

    def __init__(self, name, path=None, st=None):
        self._archived = None
        self._hidden = None
        self._system = None

        self.name = basename(name)
        self.path = path or fullpath(name)

        if not st:
            st = lstat(name)

        self.mode = S_IMODE(st.st_mode)
        self.type = S_IFMT(st.st_mode)
        self.dev = st.st_dev
        self.size = st.st_size
        try:
            self.mtime = st.st_mtime_ns
        except AttributeError:
            self.mtime = st.st_mtime

    def is_archived(self):
        if self._archived is None:
            self._archived = is_archived(self.path)
        return self._archived

    def is_hidden(self):
        if self._hidden is None:
            self._hidden = is_hidden(self.path)
        return self._hidden

    def is_system(self):
        if self._system is None:
            self._system = is_system(self.path)
        return self._system


class SkipException(Exception):
    """
    Skip Exception
    """
    pass
