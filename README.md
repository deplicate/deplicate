<p align="center"><a href="#"><img src="banner.png" alt="deplicate" /></a></p>
<p align="center"><b>Advanced Duplicate File Finder for Python.</b> <i>Nothing is impossible to solve.</i></p>


Table of contents
-----------------

- [Status](#status)
- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Quick Examples](#quick-examples)
  - [Advanced Examples](#advanced-examples)
- [API Reference](#api-reference)
  - [Properties](#properties)
  - [Methods](#methods)


Status
------

[![Travis Build Status](https://travis-ci.org/vuolter/deplicate.svg?branch=master)](https://travis-ci.org/vuolter/deplicate)
[![Requirements Status](https://requires.io/github/vuolter/deplicate/requirements.svg?branch=master)](https://requires.io/github/vuolter/deplicate/requirements/?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/bc7b97415617404694a07f2529147f7e)](https://www.codacy.com/app/deplicate/deplicate?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=vuolter/deplicate&amp;utm_campaign=Badge_Grade)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/vuolter/deplicate/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/vuolter/deplicate/?branch=master)

[![PyPI Status](https://img.shields.io/pypi/status/deplicate.svg)](https://pypi.python.org/pypi/deplicate)
[![PyPI Version](https://img.shields.io/pypi/v/deplicate.svg)](https://pypi.python.org/pypi/deplicate)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/deplicate.svg)](https://pypi.python.org/pypi/deplicate)
[![PyPI License](https://img.shields.io/pypi/l/deplicate.svg)](https://pypi.python.org/pypi/deplicate)


Description
-----------

**deplicate** is an high-performance multi-filter duplicate file finder
written in Pure Python with low memory impact and several advanced features.

Use **deplicate** to find out all the duplicated files in one or more
directories, you can also scan a bunch of files directly.
Latest releases let you to delete the founded duplicates or apply a custom
action on them when purging.

_From what we know, it's the most complete and fastest duplicate finder tool
for Python, nowadays._


Features
--------

- [x] Optimized for speed
- [x] N-tree layout for low memory consumption
- [x] Multi-threaded (partially)
- [x] Raw drive data access to maximize I/O performances (Unix only)
- [x] xxHash algorithm for fast file identification
- [x] File size and signature checking for quick duplicate exclusion
- [x] Extended file attributes scanning
- [x] Multi-filtering
- [x] Full error handling
- [x] Unicode decoding
- [x] Safe from directory recursion loop
- [ ] SSD detection
- [x] Dulicates purging
- [x] Support for moving dulicates to trash/recycle bin
- [x] Custom aation handling over deletion
- [x] Command Line Interface (https://github.com/vuolter/deplicate-cli)
- [x] Unified structured result
- [x] Support posix_fadvise
- [ ] Graphical User Interface
- [ ] Incremental file chunk checking
- [ ] Hard-link scanning
- [ ] Duplicate directories recognition
- [ ] Multi-processing
- [ ] Fully documented
- [ ] PyPy support
- [ ] ~~Exif data scanning~~


Installation
------------

Type in your command shell **with _administrator/root_ privileges**:

    pip install deplicate

In Unix-based systems, this is generally achieved by superseding
the command `sudo`.

    sudo pip install deplicate

If the above commands fail, consider installing it with the option
[`--user`](https://pip.pypa.io/en/latest/user_guide/#user-installs):

    pip install --user deplicate

> **Note:**
> You can install **deplicate** with its _Command Line Interface_ typing
> `pip install deplicate[cli]`

If in your system missing the command `pip`, but you're sure you have installed
the [Python Interpreter](https://www.python.org) and the package `setuptools`
(>=20.8.1), you can try to install **deplicate** from the sources, in this way:

1. Get the latest tarball of the source code in format
[ZIP](https://github.com/vuolter/deplicate/archive/master.zip) or
[TAR](https://github.com/vuolter/deplicate/archive/master.tar.gz).
2. Extract the downloaded archive.
3. From the extracted path, launch the command
`python setup.py install`.


Usage
-----

Import in your script the module `duplicate`.

    import duplicate

Call its function `find` if you want to know what are the duplicate files
or `purge` if you want in addition to remove them.

    duplicate.find('/path')

    duplicate.purge('/path')

In both cases, you'll get a `duplicate.ResultInfo` object,
with following properties:
- `dups` – Tuples of paths of duplicate files.
- `deldups` – Tuple of paths of purged duplicate files.
- `duperrors` – Tuple of paths of files not filtered due errors.
- `scanerrors` – Tuple of paths of files not scanned due errors.
- `delerrors` – Tuple of paths of files not purged due errors.

> **Note:**
> By default directory paths are scanned recursively.

> **Note:**
> By default files smaller than **100 MiB** or bigger than **100 GiB**
> are not scanned.

> **Note:**
> File paths are returned in canonical form.

> **Note:**
> Tuples of duplicate files are sorted in descending order according
input priority, file modification time and name length.

### Quick Examples

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

### Advanced Examples

Scan **not-recursively**:

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

Scan excluding files with extension `.doc`:

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

Scan for duplicates and apply a custom action (printing), instead purging:

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
apply a custom action (moving to path), instead purging:

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

- duplicate.`SkipException`(*args, **kwargs)
  - **Description**: Raised to skip file scanning, filtering or purging.
  - **Return**: Self instance.
  - **Parameters**: Same as built-in `Exception`.
  - **Proprieties**: Same as built-in `Exception`.
  - **Methods**: Same as built-in `Exception`.

### Classes

- duplicate.`Cache`(maxlen=`DEFAULT_MAXLEN`)
  - **Description**: Internal shared cache class.
  - **Return**: Self instance.
  - **Parameters**:
    - `maxlen` – Maximum number of entries stored.
  - **Proprieties**:
    - `DEFAULT_MAXLEN`:
      - **Description**: Default maximum number of entries stored.
      - **Value**: `128`.
  - **Methods**:
    - ...
    - `clear`(self):
      - **Description**: Clear the cache if not acquired by any object.
      - **Return**: `True` if went cleared, otherwise `False`.
      - **Parameters**: None.

- duplicate.`Deplicate`(paths,
  minsize=`DEFAULT_MINSIZE`,
  maxsize=`DEFAULT_MAXSIZE`,
  include=`None`, exclude=`None`,
  comparename=`False`, comparemtime=`False`, comparemode=`False`,
  recursive=`True`, followlinks=`False`, scanlinks=`False`,
  scanempties=`False`,
  scansystem=`True`, scanarchived=`True`, scanhidden=`True`)
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
      (including hard-links).
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
  - **Proprieties**:
    - `DEFAULT_MINSIZE`:
      - **Description**: Minimum size of files to include in scanning
        (in bytes).
      - **Value**: `102400`.
    - `DEFAULT_MAXSIZE`:
      - **Description**: Maximum size of files to include in scanning
        (in bytes).
      - **Value**: `107374182400`.
    - `result`:
        - **Description**: Result of `find` or `purge` invocation
          (by default is `None`).
        - **Value**: `duplicate.ResultInfo`.
  - **Methods**:
    - `find`(self, onerror=`None`, notify=`None`):
      - **Description**: Find duplicate files.
      - **Return**: None.
      - **Parameters**:
        - `onerror` – _(optional)_ Callback function called with two arguments,
          `exception` and `filename`, when an error occurs during file
          scanning or filtering.
        - `notify` – _(internal)_ Notifier callback.
    - `purge`(self, trash=`True`, ondel=`None`, onerror=`None`,
      notify=`None`):
      - **Description**: Find and purge duplicate files.
      - **Return**: None.
      - **Parameters**:
        - `trash` – _(optional)_ Move duplicate files to trash/recycle bin,
          instead deleting.
        - `ondel` – _(optional)_ Callback function called with one arguments,
          `filename`, before purging a duplicate file.
        - `onerror` – _(optional)_ Callback function called with two arguments,
          `exception` and `filename`, when an error occurs during file
          scanning, filtering or purging.
        - `notify` – _(internal)_ Notifier callback.

- duplicate.`ResultInfo`(dupinfo, delduplist, scnerrlist, delerrors)
  - **Description**: Duplicate result class.
  - **Return**: `collections.namedtuple`('ResultInfo',
    'dups deldups duperrors scanerrors delerrors').
  - **Parameters**:
    - `dupinfo` – _(internal)_ Instance of `duplicate.structs.DupInfo`.
    - `delduplist` – _(internal)_ Iterable of purged files
      (deleted or trashed).
    - `scnerrlist` – _(internal)_ Iterable of files not scanned (due errors).
    - `delerrors` – _(internal)_ Iterable of files not purged (due errors).
  - **Proprieties**: Same as `collections.namedtuple`.
  - **Methods**: Same as `collections.namedtuple`.

### Functions

- duplicate.`find`(*paths,
  minsize=`duplicate.Deplicate.DEFAULT_MINSIZE`,
  maxsize=`duplicate.Deplicate.DEFAULT_MAXSIZE`,
  include=`None`, exclude=`None`,
  comparename=`False`, comparemtime=`False`, comparemode=`False`,
  recursive=`True`, followlinks=`False`, scanlinks=`False`,
  scanempties=`False`,
  scansystem=`True`, scanarchived=`True`, scanhidden=`True`,
  onerror=`None`, notify=`None`)
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
      (including hard-links).
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
    - `onerror` – _(optional)_ Callback function called with two arguments,
      `exception` and `filename`, when an error occurs during file scanning or
      filtering.
    - `notify` – _(internal)_ _(optional)_ Notifier callback.

- duplicate.`purge`(*paths,
  minsize=`duplicate.Deplicate.DEFAULT_MINSIZE`,
  maxsize=`duplicate.Deplicate.DEFAULT_MAXSIZE`,
  include=`None`, exclude=`None`,
  comparename=`False`, comparemtime=`False`, comparemode=`False`,
  recursive=`True`, followlinks=`False`, scanlinks=`False`,
  scanempties=`False`,
  scansystem=`True`, scanarchived=`True`, scanhidden=`True`,
  trash=`True`, ondel=`None`, onerror=`None`, notify=`None`)
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
      (including hard-links).
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
    - `trash` – _(optional)_ Move duplicate files to trash/recycle bin,
      instead deleting.
    - `ondel` – _(optional)_ Callback function called with one arguments,
      `filename`, before purging a duplicate file.
    - `onerror` – _(optional)_ Callback function called with two arguments,
      `exception` and `filename`, when an error occurs during file scanning,
      filtering or purging.
    - `notify` – _(internal)_ _(optional)_ Notifier callback.


------------------------------------------------
###### © 2017 Walter Purcaro <vuolter@gmail.com>
