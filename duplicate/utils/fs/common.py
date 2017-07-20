# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import shutil

from contextlib import contextmanager
from os.path import (lexists, expanduser, isfile, islink, ismount,
                     realpath)
from stat import S_ISDIR, S_ISLNK, S_ISREG

import psutil
import send2trash
import xxhash

from ..init import is_os64

try:
    import directio
except ImportError:
    directio = None

try:
    from os import scandir
except ImportError:
    from scandir import scandir


_xxhash_xxh = xxhash.xxh64 if is_os64 else xxhash.xxh32


def fullpath(path):
    return realpath(expanduser(path))


def fsdecode(path):
    try:
        upath = unicode(path)
    except NameError:
        upath = os.fsdecode(path)
    return upath


def _stat(path):
    try:
        mode = os.lstat(path).st_mode

    except AttributeError:
        mode = os.stat(path).st_mode
        link = False

    else:
        link = S_ISLNK(mode)

    return mode, link


def splitpaths(iterable, followlinks=False):
    dirs = []
    files = []
    links = []
    nodes = []
    unexs = []

    for path in iterable:
        try:
            mode, symlink = _stat(path)

        except OSError:
            unexs.append(path)

        else:
            if S_ISDIR(mode):
                if not followlinks and symlink:
                    continue
                dirs.append(path)

            elif S_ISREG(mode):
                (links if symlink else files).append(path)

            else:
                nodes.append(path)

    return dirs, files, links, nodes, unexs


def _scaniter(iterable, onerror):
    while True:
        try:
            try:
                yield next(iterable)
            except StopIteration:
                break

        except (IOError, OSError) as exc:
            if onerror is not None:
                onerror(exc)
            return


def _scandir(path, onerror, followlinks):
    dirs = []
    files = []
    links = []

    try:
        scandir_it = scandir(path)

    except (IOError, OSError) as exc:
        if onerror is not None:
            onerror(exc)
        return

    try:
        for entry in _scaniter(scandir_it, onerror):

            if entry.is_file(follow_symlinks=False):
                files.append(entry)

            elif entry.is_dir(followlinks):
                dirs.append(entry)

            elif entry.is_file():
                links.append(entry)

        return dirs, files, links

    finally:
        try:
            scandir_it.close()
        except AttributeError:
            pass


def _walk(seen, path, onerror, followlinks):
    if path in seen:
        return

    dirs, files, links = _scandir(path, onerror, followlinks)
    yield dirs, files, links

    seen.add(path)

    #: Recurse into sub-directories
    for entry in dirs:
        dirpath = entry.path

        if dirpath in seen:
            continue

        for dirs, files, links in _walk(seen, dirpath, onerror, followlinks):
            yield dirs, files, links


def walk(dirname, onerror=lambda exc: None, followlinks=False, scout=None):
    if not scout:
        scout = set()
    path = fullpath(dirname)
    return _walk(scout, path, onerror, followlinks)


def mountpoint(path):
    dirname = os.path.dirname

    head = dirname(fullpath(path))
    while not ismount(head):
        head = dirname(head)

    return head


def blkdevice(path):
    partitions = psutil.disk_partitions()
    mount = mountpoint(path)

    if os.name == 'nt':
        mount = mount.upper()

    device = next(dp.device for dp in partitions if dp.mountpoin == mount)
    block = device.rsplit('/', 1)[-1]

    return block


def _readflags(sequential, direct):
    flags = os.O_RDONLY
    try:
        flags |= os.O_BINARY
        if sequential is not None:
            flags |= os.O_SEQUENTIAL if sequential else os.O_RANDOM

    except AttributeError:
        pass

    try:
        if direct:
            flags |= os.O_DIRECT
            read = directio.read
        else:
            raise AttributeError

    except AttributeError:
        read = os.read

    return read, flags


def _read(fd, fn, sequential, direct):
    try:
        if direct:
            if sequential is not None:
                fadv_sequential = os.POSIX_FADV_SEQUENTIAL
                fadv_random = os.POSIX_FADV_RANDOM
                advice = fadv_sequential if sequential else fadv_random
                os.posix_fadvise(fd, 0, 0, advice)

            def read(buf):
                data = fn(fd, buf)
                os.posix_fadvise(fd, read.offset, buf, os.POSIX_FADV_DONTNEED)
                read.offset += buf
                return data

            # NOTE: `nonlocal` statement is not available in Python 2.
            read.offset = 0

        else:
            raise AttributeError

    except AttributeError:
        def read(buf):
            return fn(fd, buf)

    return read, fd


@contextmanager
def readopen(filename, sequential=None, direct=False):
    read, flags = _readflags(sequential, direct)

    fd = os.open(filename, flags)
    try:
        yield _read(fd, read, sequential, direct)

    finally:
        os.close(fd)


def signature(filename):
    with readopen(filename) as (read, _):
        data = read(261)
    return _xxhash_xxh(data).hexdigest()


def _chunksum(fd, read, size, buffer, whence):
    buf0, buf1 = buffer
    offset, how = whence

    x = _xxhash_xxh()
    update = x.update

    if offset:
        os.lseek(fd, offset, how)

    left = size
    data = read(buf0)
    while left and data:
        update(data)
        left -= buf0
        data = read(buf0)

    if buf1:
        data = read(buf1)
        update(data)

    return x.hexdigest()


def sidesum(filename, chksize, bufsize, offset=0):
    if bufsize < chksize:
        buffer = (bufsize, chksize % bufsize)
    else:
        buffer = (chksize, 0)

    offset = abs(offset)

    with readopen(filename, sequential=False, direct=True) as (read, fd):
        whence = (offset, os.SEEK_SET)
        header = _chunksum(fd, read, chksize, buffer, whence)

        whence = (-chksize - offset, os.SEEK_END)
        footer = _chunksum(fd, read, chksize, buffer, whence)

    return header, footer


def checksum(filename, bufsize):
    x = _xxhash_xxh()
    update = x.update

    with readopen(filename, sequential=True, direct=True) as (read, _):
        data = read(bufsize)
        while data:
            update(data)
            data = read(bufsize)

    return x.hexdigest()


def remove(path, trash=False, ignore_errors=False):
    if ignore_errors and not lexists(path):
        return None

    if islink(path):
        os.unlink(path)

    elif trash:
        send2trash.send2trash(path)

    elif isfile(path):
        os.remove(path)

    else:
        shutil.rmtree(path, ignore_errors)
