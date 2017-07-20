# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .core import cache, filterdups, purgedups, scandups
from .structs import FilterType, ResultInfo
from .utils import compilecards


class Deplicate(object):

    __slots__ = ['_deldups', '_delerrors', '_dupinfo', '_scnerrors',
                 'cmpflags', 'followlinks', 'matchers', 'paths', 'recursive',
                 'result', 'scanlinks', 'scnflags', 'sizes']

    #: bytes
    DEFAULT_MINSIZE = 100 << 10
    DEFAULT_MAXSIZE = 100 << 30

    def __init__(self, paths, minsize=DEFAULT_MINSIZE, maxsize=DEFAULT_MAXSIZE,
                 include=None, exclude=None,
                 comparename=False, comparemtime=False, comparemode=False,
                 recursive=True, followlinks=False, scanlinks=False,
                 scanempties=False, scansystem=True, scanarchived=True,
                 scanhidden=True):

        if not paths:
            raise ValueError('Paths must not be empty')

        self._dupinfo = None
        self._deldups = None
        self._scnerrors = None
        self._delerrors = None

        self.result = None

        self.paths = paths
        self.sizes = (int(minsize), int(maxsize))
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

        if notify is None:
            progress_p = progress_m = progress_n = None
        else:
            def progress_p(value):
                notify('filtering files by permission mode', value)

            def progress_m(value):
                notify('filtering files by modification time', value)

            def progress_n(value):
                notify('filtering files by name', value)

        if comparemode:
            filterdups(FilterType.MODE, self._dupinfo, onerror, progress_p)

        if comparemtime:
            filterdups(FilterType.MTIME, self._dupinfo, onerror, progress_m)

        if comparename:
            filterdups(FilterType.NAME, self._dupinfo, onerror, progress_n)

    def _iofilter(self, onerror, notify):

        if notify is None:
            progress_s = progress_r = progress_h = progress_c = None
        else:
            def progress_s(value):
                notify('filtering files by signature', value)

            def progress_r(value):
                notify('filtering files by rule', value)

            def progress_h(value):
                notify('filtering files by hash', value)

            def progress_c(value):
                notify('filtering files by content', value)

        try:
            cache.acquire()

            filterdups(FilterType.SIGNATURE, self._dupinfo, onerror,
                       progress_s)
            filterdups(FilterType.RULE, self._dupinfo, onerror, progress_r)
            filterdups(FilterType.HASH, self._dupinfo, onerror, progress_h)
            filterdups(FilterType.BINARY, self._dupinfo, onerror, progress_c)

        finally:
            cache.release()

    def _scan(self, onerror, notify):

        if notify is None:
            progress = None
        else:
            def progress(value):
                notify('scanning for similar files', value)

        self._dupinfo, self._scnerrors = scandups(
            self.paths, self.sizes, self.matchers,
            self.recursive, self.followlinks, self.scanlinks, self.scnflags,
            onerror, progress)

        self._deldups = []
        self._delerrors = []

    def _purge(self, trash, ondel, onerror, notify):

        if notify is None:
            progress = None
        else:
            def progress(value):
                notify('purging duplicates', value)

        self._deldups, self._delerrors = purgedups(
            self._dupinfo, trash, ondel, onerror, progress)

    def _filter(self, onerror, notify):
        self._cpufilter(onerror, notify)
        self._iofilter(onerror, notify)

    def _find(self, onerror, notify):
        self._scan(onerror, notify)
        self._filter(onerror, notify)

    def _result(self, notify):
        if notify is not None:
            notify('finalizing results')

        self.result = ResultInfo(
            self._dupinfo, self._deldups, self._scnerrors, self._delerrors)

        #: Cleanup
        self._dupinfo = None
        self._deldups = None
        self._scnerrors = None
        self._delerrors = None

    def find(self, onerror=None, notify=None):
        if self.result is not None:
            raise RuntimeError('duplicates can only be found once')

        self._find(onerror, notify)
        self._result(notify)

    def purge(self, trash=True, ondel=None, onerror=None, notify=None):

        if self.result is not None:
            raise RuntimeError('duplicates can only be found once')

        self._find(onerror, notify)
        self._purge(trash, ondel, onerror, notify)
        self._result(notify)
