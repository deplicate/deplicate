deplicate
=========

Installation
------------

Type in your command shell **with *administrator/root* privileges**:

::

    pip install deplicate[full]

In Unix-based systems, this is generally achieved by superseding the
command ``sudo``.

::

    sudo pip install deplicate[full]

The option ``full`` ensures that all the optional packages will
downloaded and installed as well as the mandatory dependencies.

You can install just the main package typing:

::

    pip install deplicate

If the above commands fail, consider installing it with the option
`--user`_:

::

    pip install --user deplicate

Usage
-----

Use **deplicate** to find out all the duplicated files in one or more
directories, you can also scan for duplicates a bunch of files directly.

To find the duplicates import in your python script the new available
module ``duplicate`` and call its function ``find``:

::

    import duplicate

    entries = ['/path/to/directory1', '/path/to/directory2', '/path/to/file1']

    duplicate.find(entries, recursive=True)

Sample result:

::

    [
        ['/path/to/dir1/file1', '/path/to/file1', '/path/to/dir2/subdir1/file1]',
        ['/path/to/dir2/file3', '/path/to/dir2/subdir1/file3']
    ]

**Note:** Result lists are sorted in descending order by length.

API Reference
-------------

-  duplicate.\ **find**\ (
      ``paths, minsize=None, include=None, exclude=None,``
      ``comparename=False, comparemtime=False,compareperms=False,``
      ``recursive=False, followlinks=False, scanlinks=False,``
      ``scanempties=False, scansystems=True, scanarchived=True,``
      ``scanhidden=True, signsize=None``)
-  **Return**: List of lists of paths of duplicate files.
-  **Parameters**:

   -  ``paths`` -- Iterable of directory or file paths.
   -  ``minsize`` -- *(optional)* Minimum size of files to include in
      scanning (default to ``DEFAULT_MINSIZE``).
   -  ``include`` -- *(optional)* Wildcard pattern of files to include in
      scanning.
   -  ``exclude`` -- *(optional)* Wildcard pattern of files to exclude
      from scanning.
   -  ``comparename`` -- *(optional)* Check file name.
   -  ``comparemtime`` -- *(optional)* Check file modification time.
   -  ``compareperms`` -- *(optional)* Check file mode (permissions).
   -  ``recursive`` -- *(optional)* Scan directory recursively.
   -  ``followlinks`` -- *(optional)* Follow symbolic links pointing to
      directory.
   -  ``scanlinks`` -- *(optional)* Scan symbolic links pointing to file.
   -  ``scanempties`` -- *(optional)* Scan empty files.
   -  ``scansystems`` -- *(optional)* Scan OS files.
   -  ``scanarchived`` -- *(optional)* Scan archived files.
   -  ``scanhidden`` -- *(optional)* Scan hidden files.
   -  ``signsize`` -- *(optional)* Size of bytes to read from file as
      signature (default to ``DEFAULT_SIGNSIZE``).

.. _--user: https://pip.pypa.io/en/latest/user_guide/#user-installs
