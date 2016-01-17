# -*- coding: utf-8 -*-

from transifex.compat import is_py2, str

import re


def slugify(value):
    """
    @param value string
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    Taken from:
    github.com/django/django/blob/master/django/template/defaultfilters.py
    """
    import unicodedata
    value = str(value)
    value = unicodedata.normalize('NFKD', value)
    if is_py2:
        value = value.encode('ascii', 'ignore')
    value = str(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)
