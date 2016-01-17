# -*- coding: utf-8 -*-

import sys

# Syntax sugar.
_ver = sys.version_info

is_py2 = (_ver[0] == 2)

if is_py2:
    str = unicode  # noqa
else:
    str = str
