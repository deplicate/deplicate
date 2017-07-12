# -*- coding: utf-8 -*-

from __future__ import absolute_import

import fnmatch
import os
import platform
import re
import stat
import subprocess
import sys
from os import lstat
from os.path import isdir, isfile, islink, ismount, splitdrive
from time import sleep

import xxhash

try:
    import directio
except ImportError:
    directio = None

try:
    from os import scandir
except ImportError:
    from scandir import scandir


_NT_WILDCARDS = (
    'Thumbs.db', 'ehthumbs.db', 'ehthumbs_vista.db', '*.stackdump',
    'Desktop.ini', '$RECYCLE.BIN/', '*.lnk')
_OSX_WILDCARDS = (
    '*.DS_Store', '.AppleDouble', '.LSOverride', 'Icon', '._*',
    '.DocumentRevisions-V100', '.fseventsd', '.Spotlight-V100',
    '.TemporaryItems', '.Trashes', '.VolumeIcon.icns',
    '.com.apple.timemachine.donotpresent', '.AppleDB', '.AppleDesktop',
    'Network Trash Folder', 'Temporary Items', '.apdisk')
_POSIX_WILDCARDS = ('*~', '.fuse_hidden*', '.directory', '.Trash-*', '.nfs*')


def from_iterable(func):
    def new(args, **kwargs):
        return func(*args, **kwargs)
    func.from_iterable = new
    return func


def fullpath(path):
    return os.path.realpath(os.path.expanduser(path))


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

    for name in iterable:
        if isdir(name):
            if not followlinks and islink(name):
                continue
            dirs.append(name)

        elif isfile(name):
            (links if islink(name) else files).append(name)

    return dirs, files, links


def compilecards(wildcards):
    translate = fnmatch.translate
    patterns = map(translate, wildcards)

    pattern = r'|'.join(patterns)
    flags = re.I if os.name == 'nt' else 0

    return re.compile(pattern, flags)


def _scaniter(iterable, onerror):
    while True:
        try:
            try:
                yield next(iterable)
            except StopIteration:
                break

        except OSError as exc:
            if onerror is not None:
                onerror(exc)
            return


def _scandir(path, onerror, followlinks):
    dirs = []
    files = []
    links = []

    try:
        scandir_it = scandir(path)

    except OSError as exc:
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
    yield files, links

    seen.add(path)

    #: Recurse into sub-directories
    for entry in dirs:
        dirpath = entry.path

        if dirpath in seen:
            continue

        for files, links in _walk(seen, dirpath, onerror, followlinks):
            yield files, links


def walk(dirname, onerror=None, followlinks=False):
    seen = set()
    path = fullpath(dirname)
    return _walk(seen, path, onerror, followlinks)


def _has_posix_hidden_attribute(filename):
    try:
        st = lstat(filename)
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
        st = lstat(filename)
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
        st = lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_ARCHIVE)

    except AttributeError:
        import win32api
        import win32con

        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_ARCHIVE

    return flag


def _has_posix_archive_attribute(filename):
    try:
        st = lstat(filename)
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
        st = lstat(filename)
        flag = bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM)

    except AttributeError:
        import win32api
        import win32con

        attributes = win32api.GetFileAttributes(filename)
        flag = attributes & win32con.FILE_ATTRIBUTE_SYSTEM

    return flag


def _get_system_wildcards():
    if os.name == 'nt':
        wildcards = _NT_WILDCARDS
    elif sys.platform == 'darwin':
        wildcards = _OSX_WILDCARDS
    else:
        wildcards = _POSIX_WILDCARDS

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


def mountpoint(path):
    dirname = os.path.dirname

    path = fullpath(dirname(path))
    while not ismount(path):
        path = dirname(path)

    return path


def blkdevice(path):
    import psutil

    partitions = psutil.disk_partitions()
    mount = mountpoint(path)

    if os.name == 'nt':
        mount = mount.upper()

    device = next(dp.device for dp in partitions if dp.mountpoin == mount)
    block = device.rsplit('/', 1)[-1]

    return block


def blksize(path):
    """
    Get optimal file system buffer size (in bytes) for I/O calls.
    """
    try:
        size = os.statvfs(path).f_bsize

    except AttributeError:
        size = _nt_blksize(path)

    return size


def _is_nt_ssd(path):
    import win32file

    flag = False

    drive = splitdrive(path).upper()
    drivetype = win32file.GetDriveType(drive)

    if drivetype == win32file.DRIVE_RAMDISK:
        flag = True

    elif drivetype in (win32file.DRIVE_FIXED, win32file.DRIVE_REMOVABLE):
        import wmi

        c = wmi.WMI()
        phy_to_part = "Win32_DiskDriveToDiskPartition"
        log_to_part = "Win32_LogicalDiskToPartition"
        index = dict((log_disk.Caption, phy_disk.Index)
                     for phy_disk in c.Win32_DiskDrive()
                     for partition in phy_disk.associators(phy_to_part)
                     for log_disk in partition.associators(log_to_part))

        c = wmi.WMI(moniker="//./ROOT/Microsoft/Windows/Storage")
        flag = bool(
            c.MSFT_PhysicalDisk(DeviceId=str(index[drive]), MediaType=4))

    return flag


def _is_osx_ssd(path):
    block = blkdevice(path)
    cmd = 'diskutil info {0} | grep "Solid State"'.format(block)
    try:
        out = subprocess.check_output(cmd)
        flag = 'y' in out.lower()

    except subprocess.CalledProcessError:
        flag = False

    return flag


def _is_posix_ssd(path):
    block = blkdevice(path)
    path = '/sys/block/{0}/queue/rotational'.format(block)
    try:
        with open(path) as fp:
            flag = bool(fp.read().strip())

    except IOError:
        flag = False

    return flag


def is_ssd(path):
    if os.name == 'nt':
        _is_ssd = _is_nt_ssd
    elif sys.platform == 'darwin':
        _is_ssd = _is_osx_ssd
    else:
        _is_ssd = _is_posix_ssd

    return _is_ssd(path)


def is_os64():
    if os.name == 'nt':
        if 'PROCESSOR_ARCHITEW6432' in os.environ:
            flag = True
        else:
            flag = os.environ['PROCESSOR_ARCHITECTURE'].endswith('64')
    else:
        flag = platform.machine().endswith('64')

    return flag


_xxhash_xxh = xxhash.xxh64 if is_os64 else xxhash.xxh32


def signature(filename, size=None):
    buf = (size or min(lstat(filename).st_size, 512)) // 2

    with open(filename, mode='rb') as fp:
        header = _xxhash_xxh(fp.read(buf))
        fp.seek(-buf, os.SEEK_END)
        footer = _xxhash_xxh(fp.read())

    return header.hexdigest(), footer.hexdigest()


def checksum(filename, bufsize=None):
    x = _xxhash_xxh()

    hbuf = x.block_size << 10
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
    update = x.update
    try:
        data = read(fd, buf)
        while data:
            update(data)
            data = read(fd, buf)

        return x.hexdigest()

    finally:
        os.close(fd)
