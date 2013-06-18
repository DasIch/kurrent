# coding: utf-8
"""
    kurrent.ast
    ~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""


class Location(object):
    def __init__(self, line, column):
        self.line = line
        self.column = column

    def __eq__(self, other):
        return self.line == other.line and self.column == other.column

    def __hash__(self):
        return hash((self.line, self.column))

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if self.line < other.line:
                return True
            elif self.line > other.line:
                return False
            else:
                return self.column < other.column
        return NotImplemented

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.line, self.column)


class ASTNode(object):
    def traverse(self):
        yield self


class ParentNode(ASTNode):
    def __init__(self, children=None):
        super(ParentNode, self).__init__()
        if children is None:
            children = []
        self.children = children

    @property
    def start(self):
        if self.children:
            return self.children[0].start

    @property
    def end(self):
        if self.children:
            return self.children[-1].end

    def traverse(self):
        yield self
        for child in self.children:
            for node in child.traverse():
                yield node


class Document(ParentNode):
    def __init__(self, filename, title=None, children=None):
        super(Document, self).__init__(children=children)
        self.filename = filename
        self.title = title


class Paragraph(ParentNode):
    pass


class ChildNode(ASTNode):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end


class Text(ChildNode):
    def __init__(self, text, start=None, end=None):
        super(Text, self).__init__(start=start, end=end)
        self.text = text


class Header(ChildNode):
    def __init__(self, text, level, start=None, end=None):
        super(Header, self).__init__(start=start, end=end)
        self.text = text
        self.level = level


class UnorderedList(ParentNode):
    pass


class OrderedList(ParentNode):
    pass


class ListItem(ParentNode):
    pass
