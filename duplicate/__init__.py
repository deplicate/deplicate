# -*- coding: utf-8 -*-
#
#          _/                   _/ _/                     _/
#     _/_/_/   _/_/   _/_/_/   _/     _/_/_/    _/_/_/ _/_/_/_/   _/_/
#  _/    _/ _/_/_/_/ _/    _/ _/ _/ _/       _/    _/   _/     _/_/_/_/
# _/    _/ _/       _/    _/ _/ _/ _/       _/    _/   _/     _/
#  _/_/_/   _/_/_/ _/_/_/   _/ _/   _/_/_/   _/_/_/     _/_/   _/_/_/
#                 _/
#                _/

from __future__ import absolute_import

from .core import CACHE
from .deplicate import Deplicate
from .structs import Cache, ResultInfo, SkipException
from .utils import from_iterable


@from_iterable
def find(*paths, **kwargs):
    onerror = kwargs.pop('onerror', None)
    notify = kwargs.pop('notify', None)

    d = Deplicate(paths, **kwargs)
    d.find(onerror, notify)

    return d.result


@from_iterable
def purge(*paths, **kwargs):
    trash = kwargs.pop('trash', True)
    ondel = kwargs.pop('ondel', None)
    onerror = kwargs.pop('onerror', None)
    notify = kwargs.pop('notify', None)

    d = Deplicate(paths, **kwargs)
    d.purge(trash, ondel, onerror, notify)

    return d.result
