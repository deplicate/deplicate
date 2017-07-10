# -*- coding: utf-8 -*-

import fnmatch
import hashlib
import os
import re
import stat
import sys

from base64 import standard_b64encode
from os import lstat
from time import sleep

try:
    import directio
except ImportError:
    directio = None

try:
    from os import scandir
except ImportError:
    from scandir import scandir


def append_to_dict(root, key, value):
    if key in root:
        root[key].append(value)
    else:
        root[key] = [value]


def fullpath(path):
    return os.path.realpath(os.path.expanduser(path))


def fsdecode(path):
    try:
        upath = os.fsdecode(path)
    except AttributeError:
        upath = str(path)
    return upath


def compilecards(wildcards):
    translate = fnmatch.translate
    patterns = map(translate, wildcards)

    pattern = r'|'.join(patterns)
    flags = re.I if os.name == 'nt' else 0

    return re.compile(pattern, flags)


def _scandir(path, followlinks):
    dirs = []
    files = []
    links = []

    scandir_it = scandir(path)
    try:
        for entry in scandir_it:
            if entry.is_dir(followlinks):
                dirs.append(entry)

            elif entry.is_file():
                (links if entry.is_symlink() else files).append(entry)

        return dirs, files, links

    finally:
        try:
            scandir_it.close()
        except AttributeError:
            pass


def _walk(seen, path, followlinks):
    if path in seen:
        return

    dirs, files, links = _scandir(path, followlinks)
    yield files, links

    seen.add(path)

    #: Recurse into sub-directories
    for entry in dirs:
        dirpath = entry.path

        if dirpath in seen:
            continue

        for files, links in _walk(seen, dirpath, followlinks):
            yield files, links


def walk(dirname, followlinks=False):
    seen = set()
    path = fullpath(dirname)
    return _walk(seen, path, followlinks)


def _has_posix_hidden_attribute(filename):
    try:
        st = os.lstat(filename)
        flag = bool(st.st_flags & stat.UF_HIDDEN)

    except AttributeError:
        flag = False

    return flag


def _has_osx_hidden_attribute(filename):
    try:
        import Foundation

        ufilename = fsdecode(filename)
        url = Foundation.NSURL.fileURLWithPath_(ufilename)
        res = url.getResourceValue_forKey_error_(
            None, Foundation.NSURLIsHiddenKey, None
        )
        flag = res[1]

    except ImportError:
        flag = _has_posix_hidden_attribute(filename)

    return flag


def _has_nt_hidden_attribute(filename):
    try:
        st = os.lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)

    except AttributeError:
        import win32api
        import win32con

        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_HIDDEN

    return flag


def is_hidden(filename):
    if os.name == 'nt':
        has_hidden_attribute = _has_nt_hidden_attribute
    elif sys.platform == 'darwin':
        has_hidden_attribute = _has_osx_hidden_attribute
    else:
        has_hidden_attribute = _has_posix_hidden_attribute

    return filename.startswith('.') or has_hidden_attribute(filename)


def _has_nt_archive_attribute(filename):
    try:
        st = os.lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_ARCHIVE)

    except AttributeError:
        import win32api
        import win32con

        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_ARCHIVE

    return flag


def _has_posix_archive_attribute(filename):
    try:
        st = os.lstat(filename)
        flag = not bool(st.st_flags & stat.SF_ARCHIVED)

    except AttributeError:
        flag = False

    return flag


def is_archived(filename):
    if os.name == 'nt':
        has_archive_attribute = _has_nt_archive_attribute
    else:
        has_archive_attribute = _has_posix_archive_attribute

    return has_archive_attribute(filename)


def _has_nt_system_attribute(filename):
    try:
        st = os.lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM)

    except AttributeError:
        import win32api
        import win32con

        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_SYSTEM

    return flag


def _get_system_wildcards():
    if os.name == 'nt':
        wildcards = (
            'Thumbs.db', 'ehthumbs.db', 'ehthumbs_vista.db', '*.stackdump',
            'Desktop.ini', '$RECYCLE.BIN/', '*.lnk')

    elif sys.platform == 'darwin':
        wildcards = (
            '*.DS_Store', '.AppleDouble', '.LSOverride', 'Icon', '._*',
            '.DocumentRevisions-V100', '.fseventsd', '.Spotlight-V100',
            '.TemporaryItems', '.Trashes', '.VolumeIcon.icns',
            '.com.apple.timemachine.donotpresent', '.AppleDB', '.AppleDesktop',
            'Network Trash Folder', 'Temporary Items', '.apdisk')

    else:
        wildcards = (
            '*~', '.fuse_hidden*', '.directory', '.Trash-*', '.nfs*')

    return wildcards


_match_system_file = compilecards(_get_system_wildcards()).match


def is_system(filename):
    flag = _has_nt_system_attribute(filename) if os.name == 'nt' else None
    return flag or bool(_match_system_file(filename))


def _nt_blksize(path):
    import win32file
    import winerror

    diskfreespace = win32file.GetDiskFreeSpace
    dirname = os.path.dirname(path)
    try:
        cluster_sectors, sector_size = diskfreespace(dirname)[:2]
        size = cluster_sectors * sector_size

    except win32file.error as e:
        if e.winerror != winerror.ERROR_NOT_READY:
            raise
        sleep(3)
        size = _nt_blksize(dirname)

    return size


def blksize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    try:
        size = os.statvfs(path).f_bsize

    except AttributeError:
        size = _nt_blksize(path)

    return size


def signature(filename, size=None):
    buf = (size or min(lstat(filename).st_size, 512)) // 2
    with open(filename, mode='rb') as fp:
        header = fp.read(buf)
        fp.seek(-buf, os.SEEK_END)
        footer = fp.read()
    return standard_b64encode(header), standard_b64encode(footer)


def checksum(filename, hashtype, bufsize=None):
    h = hashlib.new(hashtype)

    hbuf = h.block_size << 10
    fsbuf = bufsize or blksize(filename)
    buf = fsbuf if fsbuf > hbuf else hbuf - hbuf % fsbuf

    try:
        flags = os.O_RDONLY | os.O_BINARY | os.O_SEQUENTIAL
    except AttributeError:
        flags = os.O_RDONLY

    try:
        flags |= os.O_DIRECT
        read = directio.read

    except AttributeError:
        read = os.read

    fd = os.open(filename, flags)
    update = h.update
    try:
        data = read(fd, buf)
        while data:
            update(data)
            data = read(fd, buf)

        return h.hexdigest()

    finally:
        os.close(fd)
