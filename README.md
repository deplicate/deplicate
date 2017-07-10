<p align="center"><a href="#"><img src="banner.png" alt="deplicate" /></a></p>

Advanced Duplicate File Finder for Python.
Nothing is impossible to solve.


Installation
------------

Type in your command shell **with _administrator/root_ privileges**:

    pip install deplicate[full]

In Unix-based systems, this is generally achieved by superseding
the command `sudo`.

    sudo pip install deplicate[full]

The option `full` ensures that all the optional packages will downloaded and
installed as well as the mandatory dependencies.

You can install just the main package typing:

    pip install deplicate

If the above commands fail, consider installing it with the option
[`--user`](https://pip.pypa.io/en/latest/user_guide/#user-installs):

    pip install --user deplicate


Usage
-----

Use **deplicate** to find out all the duplicated files in one or more
directories, you can also scan for duplicates a bunch of files directly.

To find the duplicates import in your python script
the new available module `duplicate` and call its method `find`:

    import duplicate

    entries = ['/path/to/directory1', '/path/to/directory2', '/path/to/file1']
    duplicate.find(entries)


Examples
--------

_TODO_


API Reference
-------------

- duplicate.**find**(`paths, minsize=None, include=None, exclude=None,
  comparename=False, comparemtime=False, compareperms=False, recursive=False,
  followlinks=False, scanlinks=False, scanempties=False, scansystems=True,
  scanarchived=True, scanhidden=True, signsize=None`)
  - **Return**: List of lists of duplicate files.
  - **Parameters**:
    - `paths` – Iterable of directory or file path.
    - `minsize` – _(optional)_ Minimum size of files to include in scanning
      (default to `DEFAULT_MINSIZE`).
    - `include` – _(optional)_ Wildcard pattern of files to include in scanning.
    - `exclude` – _(optional)_ Wildcard pattern of files to exclude
      from scanning.
    - `comparename` – _(optional)_ Check file name.
    - `comparemtime` – _(optional)_ Check file modification time.
    - `compareperms` – _(optional)_ Check file mode (permissions).
    - `recursive` – _(optional)_ Scan directory recursively.
    - `followlinks` – _(optional)_ Follow symbolic links pointing to directory.
    - `scanlinks` – _(optional)_ Scan symbolic links pointing to file.
    - `scanempties` – _(optional)_ Scan empty files.
    - `scansystems` – _(optional)_ Scan OS files.
    - `scanarchived` – _(optional)_ Scan archived files.
    - `scanhidden` – _(optional)_ Scan hidden files.
    - `signsize` – _(optional)_ Size of bytes to read from file as signature
      (default to `DEFAULT_SIGNSIZE`).


------------------------------------------------
###### © 2017 Walter Purcaro <vuolter@gmail.com>
