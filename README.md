<div align="center">
  <a href="#">
    <img src="media/banner.png?raw=true" alt="deplicate" />
  </a>
  <h2>Advanced Duplicate File Finder for Python</h2>
  <a href="https://pypi.python.org/pypi/deplicate">
    <img src="https://img.shields.io/pypi/status/deplicate.svg" alt="PyPI Status" />
  </a>
  <a href="https://pypi.python.org/pypi/deplicate">
    <img src="https://img.shields.io/pypi/v/deplicate.svg" alt="PyPI Version" />
  </a>
  <a href="https://pypi.python.org/pypi/deplicate">
    <img src="https://img.shields.io/pypi/pyversions/deplicate.svg" alt="PyPI Python Versions" />
  </a>
  <a href="https://pypi.python.org/pypi/deplicate">
    <img src="https://img.shields.io/pypi/l/deplicate.svg" alt="PyPI License" />
  </a>
  <h5><i>Nothing is impossible to solve.</i><h5>
</div>


Table of contents
-----------------

- [Status](#status)
- [Description](#description)
- [Features](#features)
- [Installation](#installation)
  - [PIP Install](#pip-install)
  - [Tarball Install](#tarball-install)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
  - [Exceptions](#exceptions)
  - [Classes](#classes)
  - [Functions](#functions)


Status
------

[![Travis Build Status](https://travis-ci.org/deplicate/deplicate.svg?branch=master)](https://travis-ci.org/deplicate/deplicate)
[![Requirements Status](https://requires.io/github/deplicate/deplicate/requirements.svg?branch=master)](https://requires.io/github/deplicate/deplicate/requirements/?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/bc7b97415617404694a07f2529147f7e)](https://www.codacy.com/app/deplicate/deplicate?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=deplicate/deplicate&amp;utm_campaign=Badge_Grade)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/deplicate/deplicate/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/deplicate/deplicate/?branch=master)


Description
-----------

**_deplicate_** is an high-performance duplicate file finder
written in Pure Python with low memory impact and several advanced filters.

Find out all the duplicate files in one or more directories,
you can also scan directly a bunch of files.
Latest releases let you to remove the spotted duplicates and/or apply a custom
action over them.


Features
--------

- [x] N-tree layout for low memory consumption
- [x] Multi-threaded (partially)
- [x] Raw drive access to maximize I/O performance (Unix only)
- [x] xxHash algorithm for fast file identification
- [x] File size and signature checking for quick duplicate exclusion
- [x] Extended file attributes scanning
- [x] Multi-filtering
- [x] Full error handling
- [x] Unicode decoding
- [x] Safe from directory walking loop
- [ ] SSD detection
- [x] Dulicates purging
- [x] Support for moving dulicates to trash/recycle bin
- [x] Custom action handling over deletion
- [x] **Command Line Interface** (https://github.com/deplicate/deplicate-cli)
- [x] Unified structured result
- [x] Support posix_fadvise
- [ ] Graphical User Interface (https://github.com/deplicate/deplicate-gui)
- [ ] Incremental file chunk checking
- [ ] Hard-link scanning
- [ ] Duplicate directories recognition
- [ ] Multi-processing
- [x] Fully documented
- [ ] PyPy support
- [ ] ~~Exif data scanning~~


Installation
------------

> **Note:**
> This will install just **_deplicate_**, without its CLI and GUI.
> - CLI _(Command Line Interface)_: https://github.com/deplicate/deplicate-cli.
> - GUI _(Graphical User Interface)_: https://github.com/deplicate/deplicate-gui.

The easiest way to install **_deplicate_** on your system is the
[PIP Install way](#pip-install),
but, if you want, you can try to install it from the sources as described in
the [Tarball Install section](#tarball-install).

### PIP Install

If the command `pip` is not found in your system,
install the latest `pip` distribution:
download [get-pip.py](https://bootstrap.pypa.io/get-pip.py)
and run it using the [Python Interpreter](https://www.python.org).

Then, type in your command shell **with _administrator/root_ privileges**:

    pip install deplicate

> **Note:**
> In Unix-based systems, you may have to type `sudo pip install deplicate`.

If the above command fails, consider installing with the option
[`--user`](https://pip.pypa.io/en/latest/user_guide/#user-installs):

    pip install --user deplicate

### Tarball Install

0. Make sure you have installed
the [Python Interpreter](https://www.python.org)
with the package `setuptools` **(>=20.8.1)**.
1. Get the latest tarball of the source code in format
[ZIP](https://github.com/deplicate/deplicate/archive/master.zip) or
[TAR](https://github.com/deplicate/deplicate/archive/master.tar.gz).
2. Extract the downloaded archive.
3. From the extracted path, execute the command
`python setup.py install`.


Usage
-----

In your script import the module `duplicate`.

    import duplicate

Call its function `find` to search the duplicate files in the given path:

    duplicate.find('/path')

Or call the function `purge` if you want to remove them in addition:

    duplicate.purge('/path')

You'll get a `duplicate.ResultInfo` object as result,
with the following properties:
- `dups` – Tuples of paths of duplicate files.
- `deldups` – Tuple of paths of purged duplicate files.
- `duperrors` – Tuple of paths of files not filtered due errors.
- `scanerrors` – Tuple of paths of files not scanned due errors.
- `delerrors` – Tuple of paths of files not purged due errors.

> **Note:**
> By default, directory paths are scanned recursively.

> **Note:**
> By default, files smaller than **100 KiB** or bigger than **100 GiB**
> are not scanned.

> **Note:**
> File paths are returned in canonical form.

> **Note:**
> Tuples of duplicate files are sorted in descending order according
input priority, file modification time and name length.

### Quick Start

Scan for duplicates a single directory:

    import duplicate

    duplicate.find('/path/to/dir')

Scan for duplicates two files (at least):

    import duplicate

    duplicate.find('/path/to/file1', '/path/to/file2')

Scan for duplicates a single directory and move them to the trash/recycle bin:

    import duplicate

    duplicate.purge('/path/to/dir')

Scan for duplicates a single directory and delete them:

    import duplicate

    duplicate.purge('/path/to/dir', trash=False)

Scan more directories together:

    import duplicate

    duplicate.find('/path/to/dir1', '/path/to/dir2', '/path/to/dir3')

Scan from iterable:

    import duplicate

    iterable = ['/path/to/dir1', '/path/to/dir2', '/path/to/dir3']

    duplicate.find.from_iterable(iterable)

Scan ignoring the minimum file size threshold:

    import duplicate

    duplicate.find('/path/to/dir', minsize=0)

### Advanced Usage

Scan without recursing directories:

    import duplicate

    duplicate.find('/path/to/file1', '/path/to/file2', '/path/to/dir1',
                   recursive=False)

> **Note:**
> In _not-recursive mode_, like the case above, directory paths are simply
> ignored.

Scan checking file names and hidden files:

    import duplicate

    duplicate.find.from_iterable('/path/to/file1', '/path/to/dir1',
                                 comparename=True, scanhidden=True)

Scan excluding files ending with extension `.doc`:

    import duplicate

    duplicate.find('/path/to/dir', exclude="*.doc")

Scan including file links:

    import duplicate

    duplicate.find('/path/to/file1', '/path/to/file2', '/path/to/file3',
                   scanlinks=True)

Scan for duplicates, handling errors with a custom action (printing):

    import duplicate

    def error_callback(exc, filename):
        print(filename)

    duplicate.find('/path/to/dir', onerror=error_callback)

Scan for duplicates and apply a custom action (printing), instead of purging:

    import duplicate

    def purge_callback(filename):
        print(filename)
        raise duplicate.SkipException

    duplicate.purge('/path/to/dir', ondel=purge_callback)

Scan for duplicates, apply a custom action (printing) and move them to
the trash/recycle bin:

    import duplicate

    def purge_callback(filename):
        print(filename)

    duplicate.purge('/path/to/dir', ondel=purge_callback)

Scan for duplicates, handling errors with a custom action (printing), and
apply a custom action (moving to path), instead of purging:

    import shutil
    import duplicate

    def error_callback(exc, filename):
        print(filename)

    def purge_callback(filename):
        shutil.move(filename, '/path/to/custom-dir')
        raise duplicate.SkipException

    duplicate.purge('/path/to/dir',
                    ondel=purge_callback, onerror=error_callback)


API Reference
-------------

### Exceptions

- duplicate.`SkipException`(_*args_, _**kwargs_)
  - **Description**: Raised to skip file scanning, filtering or purging.
  - **Return**: Self instance.
  - **Parameters**: Same as built-in `Exception`.
  - **Proprieties**: Same as built-in `Exception`.
  - **Methods**: Same as built-in `Exception`.

### Classes

- duplicate.`Cache`(_maxlen_=`DEFAULT_MAXLEN`)
  - **Description**: Internal shared cache class.
  - **Return**: Self instance.
  - **Parameters**:
    - `maxlen` – Maximum number of entries stored.
  - **Proprieties**:
    - `DEFAULT_MAXLEN`
      - **Description**: Default maximum number of entries stored.
      - **Value**: `128`.
  - **Methods**:
    - ...
    - `clear`(_self_)
      - **Description**: Clear the cache if not acquired by any object.
      - **Return**: `True` if went cleared, otherwise `False`.
      - **Parameters**: None.

- duplicate.`Deplicate`(_paths_,
    _minsize_=`DEFAULT_MINSIZE`,
    _maxsize_=`DEFAULT_MAXSIZE`,
    _include_=`None`, _exclude_=`None`,
    _comparename_=`False`, _comparemtime_=`False`, _comparemode_=`False`,
    _recursive_=`True`, _followlinks_=`False`, _scanlinks_=`False`,
    _scanempties_=`False`,
    _scansystem_=`True`, _scanarchived_=`True`, _scanhidden_=`True`)
  - **Description**: Duplicate main class.
  - **Return**: Self instance.
  - **Parameters**:
    - `paths` – Iterable of directory and/or file paths.
    - `minsize` – _(optional)_ Minimum size in bytes of files to include
      in scanning.
    - `maxsize` – _(optional)_ Maximum size in bytes of files to include
      in scanning.
    - `include` – _(optional)_ Wildcard pattern of files to include
      in scanning.
    - `exclude` – _(optional)_ Wildcard pattern of files to exclude
      from scanning.
    - `comparename` – _(optional)_ Check file name.
    - `comparemtime` – _(optional)_ Check file modification time.
    - `compareperms` – _(optional)_ Check file mode (permissions).
    - `recursive` – _(optional)_ Scan directory recursively.
    - `followlinks` – _(optional)_ Follow symbolic links pointing to directory.
    - `scanlinks` – _(optional)_ Scan symbolic links pointing to file
      (hard-links included).
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
  - **Proprieties**:
    - `DEFAULT_MINSIZE`
      - **Description**: Minimum size of files to include in scanning
        (in bytes).
      - **Value**: `102400`.
    - `DEFAULT_MAXSIZE`
      - **Description**: Maximum size of files to include in scanning
        (in bytes).
      - **Value**: `107374182400`.
    - `result`
        - **Description**: Result of `find` or `purge` invocation
          (by default is `None`).
        - **Value**: `duplicate.ResultInfo`.
  - **Methods**:
    - `find`(_self_, _onerror_=`None`, _notify_=`None`)
      - **Description**: Find duplicate files.
      - **Return**: None.
      - **Parameters**:
        - `onerror` – _(optional)_ Callback function called with two arguments,
          `exception` and `filename`, when an error occurs during file
          scanning or filtering.
        - `notify` – _(internal)_ Notifier callback.
    - `purge`(_self_,
        _trash_=`True`, _ondel_=`None`, _onerror_=`None`, _notify_=`None`)
      - **Description**: Find and purge duplicate files.
      - **Return**: None.
      - **Parameters**:
        - `trash` – _(optional)_ Move duplicate files to trash/recycle bin,
          instead of deleting.
        - `ondel` – _(optional)_ Callback function called with one arguments,
          `filename`, before purging a duplicate file.
        - `onerror` – _(optional)_ Callback function called with two arguments,
          `exception` and `filename`, when an error occurs during file
          scanning, filtering or purging.
        - `notify` – _(internal)_ Notifier callback.

- duplicate.`ResultInfo`(_dupinfo_, _delduplist_, _scnerrlist_, _delerrors_)
  - **Description**: Duplicate result class.
  - **Return**: `collections.namedtuple`(`'ResultInfo'`,
    `'dups deldups duperrors scanerrors delerrors'`).
  - **Parameters**:
    - `dupinfo` – _(internal)_ Instance of `duplicate.structs.DupInfo`.
    - `delduplist` – _(internal)_ Iterable of purged files
      (deleted or trashed).
    - `scnerrlist` – _(internal)_ Iterable of files not scanned (due errors).
    - `delerrors` – _(internal)_ Iterable of files not purged (due errors).
  - **Proprieties**: Same as `collections.namedtuple`.
  - **Methods**: Same as `collections.namedtuple`.

### Functions

- duplicate.`find`(_*paths_,
    _minsize_=`duplicate.Deplicate.DEFAULT_MINSIZE`,
    _maxsize_=`duplicate.Deplicate.DEFAULT_MAXSIZE`,
    _include_=`None`, _exclude_=`None`,
    _comparename_=`False`, _comparemtime_=`False`, _comparemode_=`False`,
    _recursive_=`True`, _followlinks_=`False`, _scanlinks_=`False`,
    _scanempties_=`False`,
    _scansystem_=`True`, _scanarchived_=`True`, _scanhidden_=`True`,
    _onerror_=`None`, _notify_=`None`)
  - **Description**: Find duplicate files.
  - **Return**: `duplicate.ResultInfo`.
  - **Parameters**:
    - `paths` – Iterable of directory and/or file paths.
    - `minsize` – _(optional)_ Minimum size in bytes of files to include
      in scanning.
    - `maxsize` – _(optional)_ Maximum size in bytes of files to include
      in scanning.
    - `include` – _(optional)_ Wildcard pattern of files to include
      in scanning.
    - `exclude` – _(optional)_ Wildcard pattern of files to exclude
      from scanning.
    - `comparename` – _(optional)_ Check file name.
    - `comparemtime` – _(optional)_ Check file modification time.
    - `compareperms` – _(optional)_ Check file mode (permissions).
    - `recursive` – _(optional)_ Scan directory recursively.
    - `followlinks` – _(optional)_ Follow symbolic links pointing to directory.
    - `scanlinks` – _(optional)_ Scan symbolic links pointing to file
      (hard-links included).
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
    - `onerror` – _(optional)_ Callback function called with two arguments,
      `exception` and `filename`, when an error occurs during file scanning or
      filtering.
    - `notify` – _(internal)_ _(optional)_ Notifier callback.

- duplicate.`purge`(_*paths_,
    _minsize_=`duplicate.Deplicate.DEFAULT_MINSIZE`,
    _maxsize_=`duplicate.Deplicate.DEFAULT_MAXSIZE`,
    _include_=`None`, _exclude_=`None`,
    _comparename_=`False`, _comparemtime_=`False`, _comparemode_=`False`,
    _recursive_=`True`, _followlinks_=`False`, _scanlinks_=`False`,
    _scanempties_=`False`,
    _scansystem_=`True`, _scanarchived_=`True`, _scanhidden_=`True`,
    _trash_=`True`, _ondel_=`None`, _onerror_=`None`, _notify_=`None`)
  - **Description**: Find and purge duplicate files.
  - **Return**: `duplicate.ResultInfo`.
  - **Parameters**:
    - `paths` – Iterable of directory and/or file paths.
    - `minsize` – _(optional)_ Minimum size in bytes of files to include
      in scanning.
    - `maxsize` – _(optional)_ Maximum size in bytes of files to include
      in scanning.
    - `include` – _(optional)_ Wildcard pattern of files to include
      in scanning.
    - `exclude` – _(optional)_ Wildcard pattern of files to exclude
      from scanning.
    - `comparename` – _(optional)_ Check file name.
    - `comparemtime` – _(optional)_ Check file modification time.
    - `compareperms` – _(optional)_ Check file mode (permissions).
    - `recursive` – _(optional)_ Scan directory recursively.
    - `followlinks` – _(optional)_ Follow symbolic links pointing to directory.
    - `scanlinks` – _(optional)_ Scan symbolic links pointing to file
      (hard-links included).
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
    - `trash` – _(optional)_ Move duplicate files to trash/recycle bin,
      instead of deleting.
    - `ondel` – _(optional)_ Callback function called with one arguments,
      `filename`, before purging a duplicate file.
    - `onerror` – _(optional)_ Callback function called with two arguments,
      `exception` and `filename`, when an error occurs during file scanning,
      filtering or purging.
    - `notify` – _(internal)_ _(optional)_ Notifier callback.


------------------------------------------------
###### © 2017 Walter Purcaro <vuolter@gmail.com>
