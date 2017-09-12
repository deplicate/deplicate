deplicate
=========

Table of contents
-----------------

-  `Description`_
-  `Features`_
-  `Installation`_
-  `PIP Install`_
-  `Tarball Install`_
-  `Usage`_
-  `Quick Start`_
-  `Advanced Usage`_
-  `API Reference`_
-  `Exceptions`_
-  `Classes`_
-  `Functions`_

Description
-----------

``deplicate`` is an high-performance duplicate file finder written in
Pure Python with low memory impact and several advanced filters.

Find out all the duplicate files in one or more directories, you can
also scan directly a bunch of files. Latest releases let you to remove
the spotted duplicates and/or apply a custom action over them.

Features
--------

-  [x] N-tree layout for low memory consumption
-  [x] Multi-threaded (partially)
-  [x] Raw drive access to maximize I/O performance (Unix only)
-  [x] xxHash algorithm for fast file identification
-  [x] File size and signature checking for quick duplicate exclusion
-  [x] Extended file attributes scanning
-  [x] Multi-filtering
-  [x] Full error handling
-  [x] Unicode decoding
-  [x] Safe from path walking loop
-  [ ] SSD detection
-  [x] Duplicates purging
-  [x] Support for moving dulicates to trash/recycle bin
-  [x] Custom action handling over deletion
-  [x] **Command Line Interface**
   (https://github.com/deplicate/deplicate-cli)
-  [x] Unified structured result
-  [x] Support posix\_fadvise
-  [ ] Graphical User Interface
   (https://github.com/deplicate/deplicate-gui)
-  [ ] Incremental file chunk checking
-  [ ] Hard-link scanning
-  [ ] Duplicate directories recognition
-  [ ] Multi-processing
-  [x] Fully documented
-  [ ] PyPy support
-  [ ] [STRIKEOUT:Exif data scanning]

Installation
------------

    **Note:** This will install just ``deplicate``, without its CLI
    and GUI.

    CLI *(Command Line Interface)*:
    https://github.com/deplicate/deplicate-cli.
    GUI *(Graphical User Interface)*:
    https://github.com/deplicate/deplicate-gui.

The easiest way to install ``deplicate`` on your system is the `PIP
Install way`_, but, if you want, you can try to install it from the
sources as described in the `Tarball Install section`_.

PIP Install
~~~~~~~~~~~

If the command ``pip`` is not found in your system, install the latest
``pip`` distribution: download `get-pip.py`_ and run it using the
`Python Interpreter`_.

Then, type in your command shell **with *administrator/root*
privileges**:

::

    pip install deplicate

In Unix-based systems, you may have to type
``sudo pip install deplicate``.


If the above command fails, consider installing with the option
`--user`_:

::

    pip install --user deplicate

Tarball Install
~~~~~~~~~~~~~~~

0. Make sure you have installed the `Python Interpreter`_ with the
   package ``setuptools`` **(>=20.8.1)**.
1. Get the latest tarball of the source code in format `ZIP`_ or `TAR`_.
2. Extract the downloaded archive.
3. From the extracted path, execute the command
   ``python setup.py install``.

Usage
-----

In your script import the module ``duplicate``.

::

    import duplicate

Call its function ``find`` to search the duplicate files in the given
path:

::

    duplicate.find('/path')

Or call the function ``purge`` if you want to remove them in addition:

::

    duplicate.purge('/path')

You’ll get a ``duplicate.ResultInfo`` object as result, with the
following properties: - ``dups`` – Tuples of paths of duplicate files. -
``deldups`` – Tuple of paths of purged duplicate files. - ``duperrors``
– Tuple of paths of files not filtered due errors. - ``scanerrors`` –
Tuple of paths of files not scanned due errors. - ``delerrors`` – Tuple
of paths of files not purged due errors.

    **Note:** By default, directory paths are scanned recursively.

    **Note:** By default, files smaller than **100 KiB** or bigger than
    **100 GiB** are not scanned.

    **Note:** File paths are returned in canonical form.

    **Note:** Tuples of duplicate files are sorted in descending order
    according input priority, file modification time and name length.

Quick Start
~~~~~~~~~~~

Scan for duplicates a single directory:

::

    import duplicate

    duplicate.find('/path/to/dir')

Scan for duplicates two files (at least):

::

    import duplicate

    duplicate.find('/path/to/file1', '/path/to/file2')

Scan for duplicates a single directory and move them to the
trash/recycle bin:

::

    import duplicate

    duplicate.purge('/path/to/dir')

Scan for duplicates a single directory and delete them:

::

    import duplicate

    duplicate.purge('/path/to/dir', trash=False)

Scan more directories together:

::

    import duplicate

    duplicate.find('/path/to/dir1', '/path/to/dir2', '/path/to/dir3')

Scan from iterable:

::

    import duplicate

    iterable = ['/path/to/dir1', '/path/to/dir2', '/path/to/dir3']

    duplicate.find.from_iterable(iterable)

Scan ignoring the minimum file size threshold:

::

    import duplicate

    duplicate.find('/path/to/dir', minsize=0)

Advanced Usage
~~~~~~~~~~~~~~

Scan without recursing directories:

::

    import duplicate

    duplicate.find('/path/to/file1', '/path/to/file2', '/path/to/dir1',
                   recursive=False)

    **Note:** In *not-recursive mode*, like the case above, directory
    paths are simply ignored.

Scan checking file names and hidden files:

::

    import duplicate

    duplicate.find.from_iterable('/path/to/file1', '/path/to/dir1',
                                 comparename=True, scanhidden=True)

Scan excluding files ending with extension ``.doc``:

::

    import duplicate

    duplicate.find('/path/to/dir', exclude="*.doc")

Scan including file links:

::

    import duplicate

    duplicate.find('/path/to/file1', '/path/to/file2', '/path/to/file3',
                   scanlinks=True)

Scan for duplicates, handling errors with a custom action (printing):

::

    import duplicate

    def error_callback(exc, filename):
        print(filename)

    duplicate.find('/path/to/dir', onerror=error_callback)

Scan for duplicates and apply a custom action (printing), instead of
purging:

::

    import duplicate

    def purge_callback(filename):
        print(filename)
        raise duplicate.SkipException

    duplicate.purge('/path/to/dir', ondel=purge_callback)

Scan for duplicates, apply a custom action (printing) and move them to
the trash/recycle bin:

::

    import duplicate

    def purge_callback(filename):
        print(filename)

    duplicate.purge('/path/to/dir', ondel=purge_callback)

Scan for duplicates, handling errors with a custom action (printing),
and apply a custom action (moving to path), instead of purging:

::

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

Exceptions
~~~~~~~~~~

-  duplicate.\ ``SkipException``\ (*\*args*, *\*\*kwargs*)
-  **Description**: Raised to skip file scanning, filtering or purging.
-  **Return**: Self instance.
-  **Parameters**: Same as built-in ``Exception``.
-  **Proprieties**: Same as built-in ``Exception``.
-  **Methods**: Same as built-in ``Exception``.

Classes
~~~~~~~

-  duplicate.\ ``Cache``\ (*maxlen*\ =\ ``DEFAULT_MAXLEN``)
-  **Description**: Internal shared cache class.
-  **Return**: Self instance.
-  **Parameters**:

   -  ``maxlen`` – Maximum number of entries stored.

-  **Proprieties**:

   -  ``DEFAULT_MAXLEN``
   -  **Description**: Default maximum number of entries stored.
   -  **Value**: ``128``.

-  **Methods**:

   -  …
   -  ``clear``\ (*self*)
   -  **Description**: Clear the cache if not acquired by any object.
   -  **Return**: ``True`` if went cleared, otherwise ``False``.
   -  **Parameters**: None.

-  duplicate.\ ``Deplicate``\ (*paths*,
   *minsize*\ =\ ``DEFAULT_MINSIZE``, *maxsize*\ =\ ``DEFAULT_MAXSIZE``,
   *include*\ =\ ``None``, *exclude*\ =\ ``None``,
   *comparename*\ =\ ``False``, *comparemtime*\ =\ ``False``,
   *comparemode*\ =\ ``False``, *recursive*\ =\ ``True``,
   *followlinks*\ =\ ``False``, *scanlinks*\ =\ ``False``,
   *scanempties*\ =\ ``False``, *scansystem*\ =\ ``True``,
   *scanarchived*\ =\ ``True``, *scanhidden*\ =\ ``True``)
-  **Description**: Duplicate main class.
-  **Return**: Self instance.
-  **Parameters**:

   -  ``paths`` – Iterable of directory and/or file paths.
   -  ``minsize`` – *(optional)* Minimum size in bytes of files to
      include in scanning.
   -  ``maxsize`` – *(optional)* Maximum size in bytes of files to
      include in scanning.
   -  ``include`` – *(optional)* Wildcard pattern of files to include in
      scanning.
   -  ``exclude`` – *(optional)* Wildcard pattern of files to exclude
      from scanning.
   -  ``comparename`` – *(optional)* Check file name.
   -  ``comparemtime`` – *(optional)* Check file modification time.
   -  ``compareperms`` – *(optional)* Check file mode (permissions).
   -  ``recursive`` – *(optional)* Scan directory recursively.
   -  ``followlinks`` – *(optional)* Follow symbolic links pointing to
      directory.
   -  ``scanlinks`` – *(optional)* Scan symbolic links pointing to file
      (hard-links included).
   -  ``scanempties`` – *(optional)* Scan empty files.
   -  ``scansystems`` – *(optional)* Scan OS files.
   -  ``scanarchived`` – *(optional)* Scan archived files.
   -  ``scanhidden`` – *(optional)* Scan hidden files.

-  **Proprieties**:

   -  ``DEFAULT_MINSIZE``
   -  **Description**: Minimum size of files to include in scanning (in
      bytes).
   -  **Value**: ``102400``.
   -  ``DEFAULT_MAXSIZE``
   -  **Description**: Maximum size of files to include in scanning (in
      bytes).
   -  **Value**: ``107374182400``.
   -  ``result``

      -  **Description**: Result of ``find`` or ``purge`` invocation (by
         default is ``None``).
      -  **Value**: ``duplicate.ResultInfo``.

-  **Methods**:

   -  ``find``\ (*self*, *onerror*\ =\ ``None``, *notify*\ =\ ``None``)
   -  **Description**: Find duplicate files.
   -  **Return**: None.
   -  **Parameters**:

      -  ``onerror`` – *(optional)* Callback function called with two
         arguments, ``exception`` and ``filename``, when an error occurs
         during file scanning or filtering.
      -  ``notify`` – *(internal)* Notifier callback.

   -  ``purge``\ (*self*, *trash*\ =\ ``True``, *ondel*\ =\ ``None``,
      *onerror*\ =\ ``None``, *notify*\ =\ ``None``)
   -  **Description**: Find and purge duplicate files.
   -  **Return**: None.
   -  **Parameters**:

      -  ``trash`` – *(optional)* Move duplicate files to trash/recycle
         bin, instead of deleting.
      -  ``ondel`` – *(optional)* Callback function called with one
         arguments, ``filename``, before purging a duplicate file.
      -  ``onerror`` – *(optional)* Callback function called with two
         arguments, ``exception`` and ``filename``, when an error occurs
         during file scanning, filtering or purging.
      -  ``notify`` – *(internal)* Notifier callback.

-  duplicate.\ ``ResultInfo``\ (*dupinfo*, *delduplist*, *scnerrlist*,
   *delerrors*)
-  **Description**: Duplicate result class.
-  **Return**: ``collections.namedtuple``\ (``'ResultInfo'``,
   ``'dups deldups duperrors scanerrors delerrors'``).
-  **Parameters**:

   -  ``dupinfo`` – *(internal)* Instance of
      ``duplicate.structs.DupInfo``.
   -  ``delduplist`` – *(internal)* Iterable of purged files (deleted or
      trashed).
   -  ``scnerrlist`` – *(internal)* Iterable of files not scanned (due
      errors).
   -  ``delerrors`` – *(internal)* Iterable of files not purged (due
      errors).

-  **Proprieties**: Same as ``collections.namedtuple``.
-  **Methods**: Same as ``collections.namedtuple``.

Functions
~~~~~~~~~

-  duplicate.\ ``find``\ (*\*paths*,
   *minsize*\ =\ ``duplicate.Deplicate.DEFAULT_MINSIZE``,
   *maxsize*\ =\ ``duplicate.Deplicate.DEFAULT_MAXSIZE``,
   *include*\ =\ ``None``, *exclude*\ =\ ``None``,
   *comparename*\ =\ ``False``, *comparemtime*\ =\ ``False``,
   *comparemode*\ =\ ``False``, *recursive*\ =\ ``True``,
   *followlinks*\ =\ ``False``, *scanlinks*\ =\ ``False``,
   *scanempties*\ =\ ``False``, *scansystem*\ =\ ``True``,
   *scanarchived*\ =\ ``True``, *scanhidden*\ =\ ``True``,
   *onerror*\ =\ ``None``, *notify*\ =\ ``None``)
-  **Description**: Find duplicate files.
-  **Return**: ``duplicate.ResultInfo``.
-  **Parameters**:

   -  ``paths`` – Iterable of directory and/or file paths.
   -  ``minsize`` – *(optional)* Minimum size in bytes of files to
      include in scanning.
   -  ``maxsize`` – *(optional)* Maximum size in bytes of files to
      include in scanning.
   -  ``include`` – *(optional)* Wildcard pattern of files to include in
      scanning.
   -  ``exclude`` – *(optional)* Wildcard pattern of files to exclude
      from scanning.
   -  ``comparename`` – *(optional)* Check file name.
   -  ``comparemtime`` – *(optional)* Check file modification time.
   -  ``compareperms`` – *(optional)* Check file mode (permissions).
   -  ``recursive`` – *(optional)* Scan directory recursively.
   -  ``followlinks`` – *(optional)* Follow symbolic links pointing to
      directory.
   -  ``scanlinks`` – *(optional)* Scan symbolic links pointing to file
      (hard-links included).
   -  ``scanempties`` – *(optional)* Scan empty files.
   -  ``scansystems`` – *(optional)* Scan OS files.
   -  ``scanarchived`` – *(optional)* Scan archived files.
   -  ``scanhidden`` – *(optional)* Scan hidden files.
   -  ``onerror`` – *(optional)* Callback function called with two
      arguments, ``exception`` and ``filename``, when an error occurs
      during file scanning or filtering.
   -  ``notify`` – \_(internal)\_ *(optional)* Notifier callback.

-  duplicate.\ ``purge``\ (*\*paths*,
   *minsize*\ =\ ``duplicate.Deplicate.DEFAULT_MINSIZE``,
   *maxsize*\ =\ ``duplicate.Deplicate.DEFAULT_MAXSIZE``,
   *include*\ =\ ``None``, *exclude*\ =\ ``None``,
   *comparename*\ =\ ``False``, *comparemtime*\ =\ ``False``,
   *comparemode*\ =\ ``False``, *recursive*\ =\ ``True``,
   *followlinks*\ =\ ``False``, *scanlinks*\ =\ ``False``,
   *scanempties*\ =\ ``False``, *scansystem*\ =\ ``True``,
   *scanarchived*\ =\ ``True``, *scanhidden*\ =\ ``True``,
   *trash*\ =\ ``True``, *ondel*\ =\ ``None``, *onerror*\ =\ ``None``,
   *notify*\ =\ ``None``)
-  **Description**: Find and purge duplicate files.
-  **Return**: ``duplicate.ResultInfo``.
-  **Parameters**:

   -  ``paths`` – Iterable of directory and/or file paths.
   -  ``minsize`` – *(optional)* Minimum size in bytes of files to
      include in scanning.
   -  ``maxsize`` – *(optional)* Maximum size in bytes of files to
      include in scanning.
   -  ``include`` – *(optional)* Wildcard pattern of files to include in
      scanning.
   -  ``exclude`` – *(optional)* Wildcard pattern of files to exclude
      from scanning.
   -  ``comparename`` – *(optional)* Check file name.
   -  ``comparemtime`` – *(optional)* Check file modification time.
   -  ``compareperms`` – *(optional)* Check file mode (permissions).
   -  ``recursive`` – *(optional)* Scan directory recursively.
   -  ``followlinks`` – *(optional)* Follow symbolic links pointing to
      directory.
   -  ``scanlinks`` – *(optional)* Scan symbolic links pointing to file
      (hard-links included).
   -  ``scanempties`` – *(optional)* Scan empty files.
   -  ``scansystems`` – *(optional)* Scan OS files.
   -  ``scanarchived`` – *(optional)* Scan archived files.
   -  ``scanhidden`` – *(optional)* Scan hidden files.
   -  ``trash`` – *(optional)* Move duplicate files to trash/recycle
      bin, instead of deleting.
   -  ``ondel`` – *(optional)* Callback function called with one
      arguments, ``filename``, before purging a duplicate file.
   -  ``onerror`` – *(optional)* Callback function called with two
      arguments, ``exception`` and ``filename``, when an error occurs
      during file scanning, filtering or purging.
   -  ``notify`` – *(internal)* *(optional)* Notifier callback.

.. _Description: #description
.. _Features: #features
.. _Installation: #installation
.. _PIP Install: #pip-install
.. _Tarball Install: #tarball-install
.. _Usage: #usage
.. _Quick Start: #quick-start
.. _Advanced Usage: #advanced-usage
.. _API Reference: #api-reference
.. _Exceptions: #exceptions
.. _Classes: #classes
.. _Functions: #functions
.. _PIP Install way: #pip-install
.. _Tarball Install section: #tarball-install
.. _get-pip.py: https://bootstrap.pypa.io/get-pip.py
.. _Python Interpreter: https://www.python.org
.. _--user: https://pip.pypa.io/en/latest/user_guide/#user-installs
.. _ZIP: https://github.com/deplicate/deplicate/archive/master.zip
.. _TAR: https://github.com/deplicate/deplicate/archive/master.tar.gz
