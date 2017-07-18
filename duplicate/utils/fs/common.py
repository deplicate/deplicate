# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import shutil
import sys

from contextlib import contextmanager
from os.path import (exists, expanduser, isdir, isfile, islink, ismount,
                     realpath)

import psutil
import send2trash
import xxhash

try:
    import directio
except ImportError:
    directio = None

try:
    from os import scandir
except ImportError:
    from scandir import scandir

from ..init import is_os64


_xxhash_xxh = xxhash.xxh64 if is_os64 else xxhash.xxh32


def fullpath(path):
    return realpath(expanduser(path))


def fsdecode(path):
    try:
        upath = unicode(path)
    except NameError:
        upath = os.fsdecode(path)
    return upath


def splitpaths(iterable, followlinks=False):
    dirs = []
    files = []
    links = []
    nodes = []
    unexs = []

    for name in iterable:
        if isdir(name):
            if not followlinks and islink(name):
                continue
            dirs.append(name)

        elif isfile(name):
            (links if islink(name) else files).append(name)

        elif exists(name):
            nodes.append(name)

        else:
            unexs.append(name)

    return dirs, files, links, nodes, unexs


def _scaniter(iterable, onerror):
    while True:
        try:
            try:
                yield next(iterable)
            except StopIteration:
                break

        except (IOError, OSError) as exc:
            onerror(exc)
            return


def _scandir(path, onerror, followlinks):
    dirs = []
    files = []
    links = []

    try:
        scandir_it = scandir(path)

    except (IOError, OSError) as exc:
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


def sidesum(filename, chksize, offset=0):
    offset = abs(offset)

    with open(filename, mode='rb') as fp:
        fp.seek(offset)
        header = fp.read(chksize)
        fp.seek(-chksize - offset, os.SEEK_END)
        footer = fp.read(chksize)

    headhash = _xxhash_xxh(header).hexdigest()
    foothash = _xxhash_xxh(footer).hexdigest()
    return headhash, foothash


@contextmanager
def readopen(filename, sequential=False, direct=False):
    try:
        flags = os.O_RDONLY

        try:
            seq = os.O_SEQUENTIAL if sequential else os.O_RANDOM
            flags |= os.O_BINARY | seq

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

        fd = os.open(filename, flags)
        yield lambda buf: read(fd, buf)

    finally:
        os.close(fd)


def signature(filename):
    with open(filename, mode='rb') as fp:
        header = fp.read(261)

    headhash = _xxhash_xxh(header).hexdigest()
    return headhash


def checksum(filename, bufsize):
    x = _xxhash_xxh()
    update = x.update

    hashsize = x.block_size << 10
    buf = bufsize if bufsize > hashsize else hashsize - hashsize % bufsize

    with readopen(filename, sequential=True, direct=True) as read:
        data = read(buf)
        while data:
            update(data)
            data = read(buf)
        return x.hexdigest()


def remove(path, trash=False, ignore_errors=False):
    if ignore_errors and not exists(path):
        return None

    if islink(path):
        os.unlink(path)
    elif trash:
        send2trash.send2trash(path)
    elif isfile(path):
        os.remove(path)
    else:
        shutil.rmtree(path, ignore_errors)
