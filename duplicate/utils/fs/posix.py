# -*- coding: utf-8 -*-

from __future__ import absolute_import

import stat

from os import lstat, statvfs

from ..init import compilecards


WILDCARDS = ('*~', '.fuse_hidden*', '.directory', '.Trash-*', '.nfs*')

_wildcards_match = compilecards(WILDCARDS).match


def blksize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    return statvfs(path).f_bsize


def has_archive_attribute(filename):
    try:
        st = lstat(filename)
        flag = not bool(st.st_flags & stat.SF_ARCHIVED)

    except AttributeError:
        flag = False

    return flag


def has_hidden_attribute(filename):
    try:
        st = lstat(filename)
        flag = bool(st.st_flags & stat.UF_HIDDEN)

    except AttributeError:
        flag = False

    return flag


is_archived = has_archive_attribute


def is_hidden(filename):
    return filename.startswith('.') or has_hidden_attribute(filename)


def is_system(filename):
    return bool(_wildcards_match(filename))
