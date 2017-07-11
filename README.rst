deplicate
=========

Table of contents
-----------------

-  `Description`_
-  `Features`_
-  `Installation`_
-  `Usage`_
-  `API Reference`_
-  `Properties`_
-  `Methods`_

Description
-----------

Use **deplicate** to find out all the duplicated files in one or more
directories, you can also scan a bunch of files directly.

**deplicate** is written in Pure Python and requires just a couple of
dependencies to work fine, depending on your system.

Features
--------

-  [x] Optimized for speed
-  [x] N-tree parsing for low memory consumation
-  [x] Multi-threaded (partially)
-  [x] Raw drive data access to maximize I/O performances
-  [x] xxHash algorithm for fast file identification
-  [x] File size and signature checking for quick duplicate exclusion
-  [x] Extended file attributes scanning
-  [x] Multi-filtering
-  [x] Error handling
-  [x] Unicode decoding
-  [x] Safe from recursion loop
-  [x] SSD detection
-  [ ] Multi-processing
-  [ ] Fully documented
-  [ ] PyPy support
-  [ ] [STRIKEOUT:Exif data scanning]

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

To find the duplicates, import in your python script the new available
module ``duplicate`` and call its function ``find``:

::

    import duplicate

    entries = ['/path/to/dir1', '/path/to/dir2', '/path/to/file1']

    duplicate.find(entries, recursive=True)

Resulting output is a list of lists of file paths, where each list
groups all the same files:

::

    [
        ['/path/to/dir1/file1', '/path/to/file1', '/path/to/dir2/subdir1/file1]',
        ['/path/to/dir2/file3', '/path/to/dir2/subdir1/file3']
    ]

**Note:** Resulting file paths are in canonical representation.

**Note:** Resulting lists are sorted in descending order by length.

API Reference
-------------

Properties
~~~~~~~~~~

-  duplicate.\ **DEFAULT\_MINSIZE**
-  **Description**: Default minimum file size in bytes.
-  **Value**: ``102400``

-  duplicate.\ **DEFAULT\_SIGNSIZE**
-  **Description**: Default file signature size in bytes.
-  **Value**: ``512``

-  duplicate.\ **MAX\_BLKSIZES\_LEN**
-  **Description**: Default maximum number of cached block size values.
-  **Value**: ``128``

Methods
~~~~~~~

-  duplicate.\ **clear\_blkcache**\ ()
-  **Description**: Clear the internal blksizes cache.
-  **Return**: None.
-  **Parameters**: None.

-  duplicate.\ **find**\ (
      ``paths, minsize=None, include=None, exclude=None, comparename=False,``
      ``comparemtime=False, compareperms=False, recursive=True,``
      ``followlinks=False, scanlinks=False, scanempties=False,``
      ``scansystems=True, scanarchived=True, scanhidden=True, signsize=None``)
-  **Description**: Find duplicate files.
-  **Return**: Nested lists of paths of duplicate files.
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

.. _Description: #description
.. _Features: #features
.. _Installation: #installation
.. _Usage: #usage
.. _API Reference: #api-reference
.. _Properties: #properties
.. _Methods: #methods
.. _--user: https://pip.pypa.io/en/latest/user_guide/#user-installs
