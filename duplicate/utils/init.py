# -*- coding: utf-8 -*-

from __future__ import absolute_import

import fnmatch
import os
import platform
import re

from contextlib import closing
from multiprocessing.pool import ThreadPool


def from_iterable(func):
    def wrapper(args, **kwargs):
        return func(*args, **kwargs)
    func.from_iterable = wrapper
    return func


def compilecards(wildcards):
    translate = fnmatch.translate

    with closing(ThreadPool()) as pool:
        patterns = pool.imap_unordered(translate, wildcards)

    pattern = r'|'.join(patterns)
    flags = re.I if os.name == 'nt' else 0

    return re.compile(pattern, flags)


def is_os64():
    if os.name == 'nt':
        if 'PROCESSOR_ARCHITEW6432' in os.environ:
            flag = True
        else:
            flag = os.environ['PROCESSOR_ARCHITECTURE'].endswith('64')
    else:
        flag = platform.machine().endswith('64')

    return flag
