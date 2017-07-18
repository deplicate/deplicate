# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import stat

from os import lstat
from time import sleep

import win32con
import winerror

import win32api
import win32file

from .common import fullpath
from ..init import compilecards


WILDCARDS = (
    'Thumbs.db', 'ehthumbs.db', 'ehthumbs_vista.db', '*.stackdump',
    'Desktop.ini', '$RECYCLE.BIN/', '*.lnk')

_wildcards_match = compilecards(WILDCARDS).match


def blksize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    diskfreespace = win32file.GetDiskFreeSpace
    dirname = os.path.dirname(fullpath(path))
    try:
        cluster_sectors, sector_size = diskfreespace(dirname)[:2]
        size = cluster_sectors * sector_size

    except win32file.error as e:
        if e.winerror != winerror.ERROR_NOT_READY:
            raise
        sleep(3)
        size = blksize(dirname)

    return size


def has_archive_attribute(filename):
    try:
        st = lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_ARCHIVE)

    except AttributeError:
        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_ARCHIVE

    return flag


def has_hidden_attribute(filename):
    try:
        st = lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)

    except AttributeError:
        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_HIDDEN

    return flag


def has_system_attribute(filename):
    try:
        st = lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM)

    except AttributeError:
        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_SYSTEM

    return flag


is_archived = has_archive_attribute


def is_hidden(filename):
    return filename.startswith('.') or has_hidden_attribute(filename)


def is_system(filename):
    return has_system_attribute(filename) or bool(_wildcards_match(filename))
