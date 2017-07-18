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
from .deplicate import Deplicate
from .structs import SkipException
from .utils import from_iterable


@from_iterable
def find(*paths, **kwargs):
    onerror = kwargs.pop('onerror')
    notify = kwargs.pop('notify')

    d = Deplicate(paths, **kwargs)
    d.find(onerror, notify)

    return d.result


@from_iterable
def purge(*paths, **kwargs):
    trash = kwargs.pop('trash', True)
    onerror = kwargs.pop('onerror')
    ondel = kwargs.pop('ondel')
    notify = kwargs.pop('notify')

    d = Deplicate(paths, **kwargs)
    d.purge(trash, ondel, onerror, notify)

    return d.result
