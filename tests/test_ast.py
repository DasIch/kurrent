# coding: utf-8
"""
    tests.test_ast
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent.ast import Location


class TestLocation(object):
    def test_init(self):
        location = Location(1, 2)
        assert location.line == 1
        assert location.column == 2

    def test_eq(self):
        assert Location(1, 1) == Location(1, 1)
        assert not (Location(1, 1) == Location(1, 2))
        assert not (Location(1, 1) == Location(2, 1))

    def test_ne(self):
        assert Location(1, 1) != Location(1, 2)
        assert Location(1, 1) != Location(2, 1)

    def test_hash(self):
        assert hash(Location(1, 1)) == hash(Location(1, 1))

    def test_repr(self):
        location = Location(1, 2)
        assert repr(location) == 'Location(1, 2)'
