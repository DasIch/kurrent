# coding: utf-8
"""
    tests.test_ast
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent.ast import (
    Location, Document, Paragraph, Text, Header, OrderedList, ListItem
)


class TestLocation(object):
    def test_init(self):
        location = Location(1, 2)
        assert location.line == 1
        assert location.column == 2

    def test_eq(self):
        assert Location(1, 1) == Location(1, 1)
        assert not (Location(1, 1) == Location(1, 2))
        assert not (Location(1, 1) == Location(2, 1))
        assert not (Location(1, 2) == Location(1, 1))
        assert not (Location(2, 1) == Location(1, 1))

    def test_ne(self):
        assert Location(1, 1) != Location(1, 2)
        assert Location(1, 1) != Location(2, 1)
        assert Location(1, 2) != Location(1, 1)
        assert Location(2, 1) != Location(1, 1)

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
        assert not (Location(1, 2) <= Location(1, 1))
        assert not (Location(2, 1) <= Location(1, 1))

        assert Location(1, 1) <= Location(1, 2)
        assert Location(1, 1) <= Location(2, 1)

        assert not (Location(2, 1) <= Location(1, 1))
        assert not (Location(1, 2) <= Location(1, 1))

    def test_ge(self):
        assert Location(1, 1) >= Location(1, 1)
        assert not (Location(1, 1) >= Location(1, 2))
        assert not (Location(1, 1) >= Location(2, 1))

        assert Location(2, 1) >= Location(1, 1)
        assert Location(1, 2) >= Location(1, 1)

        assert not (Location(1, 1) >= Location(2, 1))
        assert not (Location(1, 1) >= Location(1, 2))

    def test_repr(self):
        location = Location(1, 2)
        assert repr(location) == 'Location(1, 2)'


class TestDocument(object):
    def test_init(self):
        document = Document('foo')
        assert document.filename == 'foo'
        assert document.title is None
        assert document.children == []
        assert document.start is None
        assert document.end is None

        document = Document('foo', title=u'bar')
        assert document.filename == 'foo'
        assert document.title == u'bar'
        assert document.children == []
        assert document.start is None
        assert document.end is None

        document = Document('foo', children=[
            Paragraph(children=[
                Text(u'foo')
            ])
        ])
        assert document.filename == 'foo'
        assert len(document.children) == 1
        assert document.start is None
        assert document.end is None

        document = Document('foo', children=[
            Paragraph(children=[
                Text(u'foo', start=Location(1, 1), end=Location(1, 2))
            ]),
            Paragraph(children=[
                Text(u'bar', start=Location(1, 2), end=Location(1, 3))
            ])
        ])
        assert document.filename == 'foo'
        assert len(document.children) == 2
        assert document.start == Location(1, 1)
        assert document.end == Location(1, 3)


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


class TestOrderedList(object):
    def test_init(self):
        ordered_list = OrderedList()
        assert ordered_list.children == []
        assert ordered_list.start is None
        assert ordered_list.end is None

        ordered_list = OrderedList(children=[
            ListItem(children=[
                Text(u'foo', start=Location(1, 1), end=Location(1, 2))
            ]),
            ListItem(children=[
                Text(u'bar', start=Location(2, 1), end=Location(2, 2))
            ])
        ])
        assert len(ordered_list.children) == 2
        assert ordered_list.start == Location(1, 1)
        assert ordered_list.end == Location(2, 2)


class TestListItem(object):
    def test_init(self):
        list_item = ListItem()
        assert list_item.children == []

        list_item = ListItem(children=[
            Text(u'foo', start=Location(1, 1), end=Location(1, 2)),
            Text(u'bar', start=Location(1, 2), end=Location(1, 3))
        ])
        assert len(list_item.children) == 2
        assert list_item.start == Location(1, 1)
        assert list_item.end == Location(1, 3)
