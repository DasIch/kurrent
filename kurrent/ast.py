# coding: utf-8
"""
    kurrent.ast
    ~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from itertools import chain


class Location(object):
    def __init__(self, line, column):
        self.line = line
        self.column = column

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.line == other.line and self.column == other.column
        return NotImplemented

    def __hash__(self):
        return hash((self.line, self.column))

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.line < other.line or
                self.line == other.line and self.column < other.column
            )
        return NotImplemented

    def __le__(self, other):
        return self < other or self == other

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.line, self.column)


class ASTNode(object):
    def __init__(self, parent=None):
        self.parent = parent

    def replace_in_parent(self, replacement):
        self.parent.replace(self, replacement)

    def traverse(self):
        yield self


class ParentNode(ASTNode):
    def __init__(self, children=None, parent=None):
        super(ParentNode, self).__init__(parent=parent)
        self.children = []

        if children is not None:
            self.add_children(children)

    @property
    def start(self):
        if hasattr(self, '_start'):
            return self._start
        if self.children:
            return self.children[0].start

    @start.setter
    def start(self, new_start):
        self._start = new_start

    @property
    def end(self):
        if hasattr(self, '_end'):
            return self._end
        if self.children:
            return self.children[-1].end

    @end.setter
    def end(self, new_end):
        self._end = new_end

    def add_child(self, node):
        node.parent = self
        self.children.append(node)

    def add_children(self, nodes):
        for node in nodes:
            self.add_child(node)

    def replace(self, old, new):
        index = self.children.index(old)
        new.parent = self
        self.children[index] = new

    def traverse(self):
        yield self
        for child in self.children:
            for node in child.traverse():
                yield node

    def __repr__(self):
        return '%s(children=%r, parent=%r)' % (
            self.__class__.__name__, self.children, self.parent
        )


class Document(ParentNode):
    def __init__(self, filename, metadata=None, children=None, parent=None):
        super(Document, self).__init__(children=children, parent=parent)
        self.filename = filename
        self.metadata = {} if metadata is None else metadata

    def __repr__(self):
        return '%s(%r, metadata=%r, children=%r, parent=%r)' % (
            self.__class__.__name__, self.filename, self.metadata,
            self.children, self.parent
        )


class Paragraph(ParentNode):
    pass


class Emphasis(ParentNode):
    pass


class Strong(ParentNode):
    pass


class ChildNode(ASTNode):
    def __init__(self, start=None, end=None, parent=None):
        super(ChildNode, self).__init__(parent=parent)
        self.start = start
        self.end = end


class Text(ChildNode):
    def __init__(self, text, start=None, end=None, parent=None):
        super(Text, self).__init__(start=start, end=end, parent=parent)
        self.text = text

    def __repr__(self):
        return '%s(%r, start=%r, end=%r, parent=%r)' % (
            self.__class__.__name__, self.text, self.start, self.end,
            self.parent
        )


class Header(ChildNode):
    def __init__(self, text, level, start=None, end=None, parent=None):
        super(Header, self).__init__(start=start, end=end, parent=parent)
        self.text = text
        self.level = level

    def __repr__(self):
        return '%s(%r, %r, start=%r, end=%r, parent=%r)' % (
            self.__class__.__name__, self.text, self.level, self.start,
            self.end, self.parent
        )


class InlineExtension(ChildNode):
    def __init__(self, type, primary, secondary=None, text=None, metadata=None,
                 start=None, end=None, parent=None):
        super(InlineExtension, self).__init__(start=start, end=end, parent=parent)
        self.type = type
        self.primary = primary
        self.secondary = secondary
        self.text = text
        self.metadata = {} if metadata is None else metadata

    def __repr__(self):
        return '%s(%r, %r, secondary=%r, text=%r, metadata=%r, start=%r, end=%r, parent=%r)' % (
            self.__class__.__name__, self.type, self.primary, self.secondary,
            self.text, self.metadata, self.start, self.end, self.parent
        )


class Extension(ChildNode):
    def __init__(self, type, primary, secondary=None, body=None, start=None,
                 end=None, parent=None):
        super(Extension, self).__init__(start=start, end=end, parent=parent)
        self.type = type
        self.primary = primary
        self.secondary = secondary
        self.body = [] if body is None else body

    def __repr__(self):
        return '%s(%r, %r, secondary=%r, body=%r, start=%r, end=%r, parent=%r)' % (
            self.__class__.__name__, self.type, self.primary, self.secondary,
            self.body, self.start, self.end, self.parent
        )


class UnorderedList(ParentNode):
    pass


class OrderedList(ParentNode):
    pass


class ListItem(ParentNode):
    pass


class BlockQuote(ParentNode):
    pass


class RawBlock(ChildNode):
    def __init__(self, body, start=None, end=None, parent=None):
        super(RawBlock, self).__init__(start=start, end=end, parent=parent)
        self.body = body

    def __repr__(self):
        return '%s(%r, start=%r, end=%r, parent=%r)' % (
            self.__class__.__name__, self.body, self.start, self.end,
            self.parent
        )


class DefinitionList(ParentNode):
    pass


class Definition(ASTNode):
    def __init__(self, term, description, parent=None):
        super(Definition, self).__init__(parent=parent)
        self.term = term
        self.description = description

    @property
    def start(self):
        return self.term[0].start

    @property
    def end(self):
        return self.description[-1].end

    def traverse(self):
        yield self
        for child in chain(self.term, self.description):
            for grandchild in child.traverse():
                yield grandchild

    def __repr__(self):
        return '%s(%r, %r, parent=%r)' % (
            self.__class__.__name__, self.term, self.description, self.parent
        )
