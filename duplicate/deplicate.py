# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .core import _MINSIZE, cache, filterdups, purgedups, scandups
from .structs import FilterType, ResultInfo
from .utils import compilecards


def _dummy_notify(text, progress=None):
    pass


def _dummy_ondel(filepath):
    pass


def _dummy_onerror(exc, filepath):
    pass


class Deplicate(object):

    __slots__ = ['_dupinfo', '_deldups', '_scnerrors', '_delerrors',
                 'result', 'paths', 'minsize', 'recursive', 'followlinks',
                 'scanlinks', 'matchers', 'scnflags', 'cmpflags']

    DEFAULT_MINSIZE = _MINSIZE

    def __init__(self, paths, minsize=DEFAULT_MINSIZE, include=None,
                 exclude=None, comparename=False, comparemtime=False,
                 comparemode=False, recursive=True, followlinks=False,
                 scanlinks=False, scanempties=False, scansystem=True,
                 scanarchived=True, scanhidden=True):

        if not paths:
            raise ValueError('Paths must not be empty')

        self._dupinfo = None
        self._deldups = None
        self._scnerrors = None
        self._delerrors = None

        self.result = None

        self.paths = paths
        self.minsize = int(minsize)
        self.recursive = recursive
        self.followlinks = followlinks
        self.scanlinks = scanlinks

        cc = compilecards
        included_match = cc(include).match if include else lambda p: True
        excluded_match = cc(exclude).match if exclude else lambda p: False

        self.matchers = (included_match, excluded_match)
        self.scnflags = (scanempties, scansystem, scanarchived, scanhidden)
        self.cmpflags = (comparename, comparemtime, comparemode)

    def _cpufilter(self, onerror, notify):
        comparename, comparemtime, comparemode = self.cmpflags

        if comparemode:
            notify('filtering files by permission mode')
            filterdups(FilterType.MODE, self._dupinfo, onerror)

        if comparemtime:
            notify('filtering files by modification time')
            filterdups(FilterType.MTIME, self._dupinfo, onerror)

        if comparename:
            notify('filtering files by name')
            filterdups(FilterType.NAME, self._dupinfo, onerror)

    def _iofilter(self, onerror, notify):
        try:
            cache.acquire()

            notify('filtering files by signature')
            filterdups(FilterType.SIGNATURE, self._dupinfo, onerror)

            notify('filtering files by rule')
            filterdups(FilterType.RULE, self._dupinfo, onerror)

            notify('filtering files by hash')
            filterdups(FilterType.HASH, self._dupinfo, onerror)

            notify('filtering files by content')
            filterdups(FilterType.BINARY, self._dupinfo, onerror)

        finally:
            cache.release()

    def _scan(self, onerror, notify):
        notify('scanning for similar files')

        self._dupinfo, self._scnerrors = scandups(
            self.paths, self.minsize, self.matchers, self.recursive,
            self.followlinks, self.scanlinks, self.scnflags, onerror)

        self._deldups = []
        self._delerrors = []

    def _purge(self, trash, ondel, onerror, notify):
        notify('purging duplicates')

        self._deldups, self._delerrors = purgedups(
            self._dupinfo, trash, ondel, onerror)

    def _filter(self, onerror, notify):
        self._cpufilter(onerror, notify)
        self._iofilter(onerror, notify)

    def _find(self, onerror, notify):
        self._scan(onerror, notify)
        self._filter(onerror, notify)

    def _result(self, notify):
        notify('finalizing results')

        self.result = ResultInfo(
            self._dupinfo, self._deldups, self._scnerrors, self._delerrors)

        self._dupinfo = None
        self._deldups = None
        self._scnerrors = None
        self._delerrors = None

    def find(self, onerror=_dummy_onerror, notify=_dummy_notify):
        if self.result is not None:
            raise RuntimeError('duplicates can only be found once')

        self._find(onerror, notify)
        self._result(notify)

    def purge(self, trash=True, ondel=_dummy_ondel, onerror=_dummy_onerror,
              notify=_dummy_notify):

        if self.result is not None:
            raise RuntimeError('duplicates can only be found once')

        self._find(onerror, notify)
        self._purge(trash, ondel, onerror, notify)
        self._result(notify)
