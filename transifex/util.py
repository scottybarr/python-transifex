# -*- coding: utf-8 -*-

import re


def force_unicode(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s

    if hasattr(s, '__unicode__'):
        s = unicode(s)
    else:
        s = unicode(str(s), encoding)

    return s


def slugify(value):
    """
    @param value string
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    Taken from:
    github.com/django/django/blob/master/django/template/defaultfilters.py
    """
    import unicodedata
    value = force_unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)
