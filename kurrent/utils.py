# coding: utf-8
"""
    kurrent.utils
    ~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from ._compat import implements_iterator


@implements_iterator
class PushableIterator(object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)
        self.remaining = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining:
            return self.remaining.pop()
        return next(self._iterator)

    def push(self, item):
        self.remaining.append(item)

    def push_many(self, items):
        for item in items:
            self.push(item)
