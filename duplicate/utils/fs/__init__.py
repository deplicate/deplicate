# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .common import *

if os.name == 'nt':
    from .nt import *

elif sys.platform == 'darwin':
    from .osx import *

else:
    from .posix import *
