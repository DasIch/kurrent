# coding: utf-8
"""
    tests.test_ast
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest

from kurrent.ast import (
    Location, Document, Paragraph, Emphasis, Strong, Text, Header,
    UnorderedList, OrderedList, ListItem, InlineExtension, Extension,
    BlockQuote, RawBlock, DefinitionList, Definition, Link
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

        assert not (Location(1, 1) == None)

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


class ASTNodeTest(object):
    @pytest.fixture
    def node(self, node_cls):
        return node_cls()

    @pytest.fixture
    def nodes(self, node_cls):
        while True:
            yield node_cls()

    def test_init(self, node_cls):
        assert node_cls().parent is None
        parent = Document('test')
        node = node_cls(parent=parent)
        assert node.parent is parent

    def test_replace_in_parent(self, nodes):
        document = Document('test')
        to_be_replaced = next(nodes)
        replacing = next(nodes)
        document.add_child(to_be_replaced)
        to_be_replaced.replace_in_parent(replacing)
        assert document.children[0] is replacing
        assert replacing.parent is document

    def test_remove_from_parent(self, node):
        document = Document('test', children=[node])
        node.remove_from_parent()
        assert not document.children


class ParentNodeTest(ASTNodeTest):
    def test_init(self, node_cls):
        super(ParentNodeTest, self).test_init(node_cls)
        node = node_cls()
        assert node.children == []
        assert node.start is None
        assert node.end is None

        a = Text(u'foo', start=Location(1, 1), end=Location(1, 4))
        b = Text(u'bar', start=Location(2, 1), end=Location(2, 4))
        node = node_cls(children=[a, b])
        assert node.children == [a, b]
        assert a.parent is node
        assert b.parent is node
        assert node.start == Location(1, 1)
        assert node.end == Location(2, 4)

    def test_start(self, node):
        assert node.start is None
        node.start = Location(1, 1)
        assert node.start == Location(1, 1)

    def test_end(self, node):
        assert node.end is None
        node.end = Location(2, 1)
        assert node.end == Location(2, 1)

    def test_add_child(self, node):
        assert not node.children
        assert node.start is None
        assert node.end is None
        child = Text(u'foo', start=Location(1, 1), end=Location(1, 4))
        assert child.parent is None
        node.add_child(child)
        assert node.children[0] is child
        assert child.parent is node
        assert node.start == Location(1, 1)
        assert node.end == Location(1, 4)

    def test_add_children(self, node):
        assert not node.children
        a = Text(u'foo', start=Location(1, 1), end=Location(1, 4))
        b = Text(u'bar', start=Location(2, 1), end=Location(2, 4))
        node.add_children([a, b])
        assert len(node.children) == 2
        assert node.children[0] is a
        assert a.parent is node
        assert node.children[1] is b
        assert b.parent is node
        assert node.start == Location(1, 1)
        assert node.end == Location(2, 4)

    def test_replace(self, node):
        to_be_replaced = Text(u'foo', start=Location(1, 1), end=Location(1, 4))
        replacing = Text(u'bar', start=Location(2, 1), end=Location(2, 4))
        node.add_child(to_be_replaced)
        assert node.start == Location(1, 1)
        assert node.end == Location(1, 4)
        node.replace(to_be_replaced, replacing)
        assert node.start == Location(2, 1)
        assert node.end == Location(2, 4)
        assert len(node.children) == 1
        assert node.children[0] is replacing
        assert replacing.parent is node

    def test_remove(self, node):
        child = Text(u'foo')
        node.add_child(child)
        assert node.children[0] is child
        node.remove(child)
        assert not node.children

    def test_repr(self, node):
        assert (
            repr(node) ==
            '%s(children=[], parent=None)' % node.__class__.__name__
        )


class TestDocument(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: Document('foo', *args, **kwargs)

    def test_init(self, node_cls):
        super(TestDocument, self).test_init(node_cls)
        document = Document('foo')
        assert document.filename == 'foo'
        assert document.metadata == {}
        assert document.children == []
        assert document.parent is None
        assert document.start is None
        assert document.end is None

        document = Document('foo', metadata={'title': u'bar'})
        assert document.filename == 'foo'
        assert document.metadata == {'title': u'bar'}
        assert document.children == []
        assert document.parent is None
        assert document.start is None
        assert document.end is None

        document = Document('foo', children=[
            Paragraph(children=[
                Text(u'foo')
            ])
        ])
        assert document.filename == 'foo'
        assert len(document.children) == 1
        assert document.children[0].parent is document
        assert document.parent is None
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
        for child in document.children:
            assert child.parent is document
        assert document.parent is None
        assert document.start == Location(1, 1)
        assert document.end == Location(1, 3)

    def test_repr(self):
        assert (
            repr(Document('foo')) ==
            "Document('foo', metadata={}, children=[], parent=None)"
        )


class TestParagraph(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return Paragraph


class TestEmphasis(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return Emphasis


class TestStrong(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return Strong


class TestText(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: Text(u'foo', *args, **kwargs)

    def test_repr(self):
        assert (
            repr(Text('foo')) ==
            "Text('foo', start=None, end=None, parent=None)"
        )


class TestHeader(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: Header(u'foo', 1, *args, **kwargs)

    @pytest.fixture
    def node(self, node_cls):
        return node_cls()

    def test_init(self, node_cls):
        super(TestHeader, self).test_init(node_cls)
        header = Header(u'foo', 1)
        assert header.text == u'foo'
        assert header.level == 1

        header = Header(u'foo', 1, start=Location(1, 1), end=Location(1, 2))
        assert header.text == u'foo'
        assert header.level == 1
        assert header.parent is None
        assert header.start == Location(1, 1)
        assert header.end == Location(1, 2)

    def test_repr(self):
        assert (
            repr(Header('foo', 1)) ==
            "Header('foo', 1, start=None, end=None, parent=None)"
        )


class TestUnorderedList(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return UnorderedList


class TestOrderedList(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return OrderedList


class TestListItem(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return ListItem


class TestInlineExtension(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: InlineExtension(
            'type', 'primary', *args, **kwargs
        )

    def test_init(self, node_cls):
        super(TestInlineExtension, self).test_init(node_cls)

        node = InlineExtension('type', 'primary')
        assert node.type == 'type'
        assert node.primary == 'primary'
        assert node.secondary is None
        assert node.text is None
        assert node.metadata == {}
        assert node.start is None
        assert node.end is None
        assert node.parent is None

        node = InlineExtension(
            'type', 'primary', secondary='secondary', text='text',
            metadata={'spam': 'eggs'}
        )
        assert node.type == 'type'
        assert node.primary == 'primary'
        assert node.secondary == 'secondary'
        assert node.text == 'text'
        assert node.metadata == {'spam': 'eggs'}

    def test_repr(self):
        assert repr(InlineExtension('type', 'primary')) == (
            "InlineExtension("
                "'type', 'primary', secondary=None, text=None, metadata={}, "
                "start=None, end=None, parent=None"
            ")"
        )


class TestExtension(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: Extension(
            'type', 'primary', *args, **kwargs
        )

    def test_init(self, node_cls):
        super(TestExtension, self).test_init(node_cls)

        node = Extension('type', 'primary')
        assert node.type == 'type'
        assert node.primary == 'primary'
        assert node.secondary is None
        assert node.body == []

        node = Extension('type', 'primary', secondary='secondary', body=['foo'])
        assert node.type == 'type'
        assert node.primary == 'primary'
        assert node.secondary == 'secondary'
        assert node.body == ['foo']

    def test_repr(self):
        assert repr(Extension('type', 'primary')) == (
            "Extension("
                "'type', 'primary', secondary=None, body=[], start=None, "
                "end=None, parent=None"
            ")"
        )


class TestBlockQuote(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return BlockQuote


class TestRawBlock(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: RawBlock([], *args, **kwargs)

    def test_init(self, node_cls):
        super(TestRawBlock, self).test_init(node_cls)
        assert RawBlock([]).body == []

    def test_repr(self):
        assert (
            repr(RawBlock([])) ==
            'RawBlock([], start=None, end=None, parent=None)'
        )


class TestDefinitionList(ParentNodeTest):
    @pytest.fixture
    def node_cls(self):
        return DefinitionList


class TestDefinition(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: Definition([], [], *args, **kwargs)

    def test_init(self, node_cls):
        super(TestDefinition, self).test_init(node_cls)
        node = Definition(['term'], ['description'])
        assert node.term == ['term']
        assert node.description == ['description']

    def test_start(self):
        node = Definition([Text(u'foo', start=Location(1, 1))], [])
        assert node.start == Location(1, 1)

    def test_end(self):
        node = Definition([], [Text(u'foo', end=Location(1, 4))])
        assert node.end == Location(1, 4)

    def test_traverse(self):
        node = Definition([Text('a'), Text('b')], [Text('c'), Text('d')])
        traversal = node.traverse()
        assert next(traversal) is node
        assert next(traversal).text == 'a'
        assert next(traversal).text == 'b'
        assert next(traversal).text == 'c'
        assert next(traversal).text == 'd'
        with pytest.raises(StopIteration):
            next(traversal)

    def test_repr(self):
        assert repr(Definition([], [])) == 'Definition([], [], parent=None)'


class TestLink(ASTNodeTest):
    @pytest.fixture
    def node_cls(self):
        return lambda *args, **kwargs: Link('target', 'text', *args, **kwargs)

    def test_repr(self):
        assert repr(Link('target', 'text')) == (
            "Link('target', 'text', start=None, end=None, parent=None)"
        )
