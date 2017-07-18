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

from .core import cache
from .deplicate import Deplicate, _dummy_notify, _dummy_ondel, _dummy_onerror
from .structs import SkipException
from .utils import from_iterable


@from_iterable
def find(*paths, **kwargs):
    onerror = kwargs.pop('onerror', _dummy_onerror)
    notify = kwargs.pop('notify', _dummy_notify)

    d = Deplicate(paths, **kwargs)
    d.find(onerror, notify)

    return d.result


@from_iterable
def purge(*paths, **kwargs):
    trash = kwargs.pop('trash', True)
    onerror = kwargs.pop('onerror', _dummy_onerror)
    ondel = kwargs.pop('ondel', _dummy_ondel)
    notify = kwargs.pop('notify', _dummy_notify)

    d = Deplicate(paths, **kwargs)
    d.purge(trash, ondel, onerror, notify)

    return d.result
