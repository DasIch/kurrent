# coding: utf-8
"""
    kurrent._compat
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys


PY2 = sys.version_info[0] == 2


_identity = lambda x: x


if PY2:
    def implements_iterator(cls):
        cls.next = cls.__next__
        del cls.__next__
        return cls

    text_type = unicode

    from itertools import ifilter
else:
    implements_iterator = _identity
    text_type = str
    ifilter = filter
