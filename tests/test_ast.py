# coding: utf-8
"""
    tests.test_ast
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent.ast import Location, Paragraph, Text, Header


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

    def test_lt(self):
        assert Location(1, 1) < Location(1, 2)
        assert Location(1, 1) < Location(2, 1)

        assert not (Location(1, 1) < Location(1, 1))
        assert not (Location(2, 1) < Location(1, 1))
        assert not (Location(1, 2) < Location(1, 1))

    def test_gt(self):
        assert Location(2, 1) > Location(1, 1)
        assert Location(1, 2) > Location(1, 1)

        assert not (Location(1, 1) > Location(1, 1))
        assert not (Location(1, 1) > Location(2, 1))
        assert not (Location(1, 1) > Location(1, 2))

    def test_le(self):
        assert Location(1, 1) <= Location(1, 1)
        assert Location(1, 1) <= Location(1, 2)
        assert Location(1, 1) <= Location(2, 1)

        assert not (Location(2, 1) <= Location(1, 1))
        assert not (Location(1, 2) <= Location(1, 1))

    def test_repr(self):
        location = Location(1, 2)
        assert repr(location) == 'Location(1, 2)'


class TestParagraph(object):
    def test_init(self):
        paragraph = Paragraph()
        assert paragraph.children == []
        assert paragraph.start is None
        assert paragraph.end is None

        paragraph = Paragraph(children=[
            Text(u'foo', start=Location(1, 1), end=Location(1, 2)),
            Text(u'bar', start=Location(1, 2), end=Location(1, 3))
        ])
        assert len(paragraph.children) == 2
        assert paragraph.start == Location(1, 1)
        assert paragraph.end == Location(1, 3)


class TestText(object):
    def test_init(self):
        text = Text(u'foo')
        assert text.text == u'foo'

        text = Text(u'foo', start=Location(1, 1), end=Location(1, 2))
        assert text.text == u'foo'
        assert text.start == Location(1, 1)
        assert text.end == Location(1, 2)


class TestHeader(object):
    def test_init(self):
        header = Header(u'foo', 1)
        assert header.text == u'foo'
        assert header.level == 1

        header = Header(u'foo', 1, start=Location(1, 1), end=Location(1, 2))
        assert header.text == u'foo'
        assert header.level == 1
        assert header.start == Location(1, 1)
        assert header.end == Location(1, 2)
