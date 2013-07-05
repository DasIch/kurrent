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


class Document(ParentNode):
    def __init__(self, filename, title=None, children=None):
        super(Document, self).__init__(children=children)
        self.filename = filename
        self.title = title


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
    def __init__(self, text, start=None, end=None):
        super(Text, self).__init__(start=start, end=end)
        self.text = text


class Header(ChildNode):
    def __init__(self, text, level, start=None, end=None):
        super(Header, self).__init__(start=start, end=end)
        self.text = text
        self.level = level


class Reference(ChildNode):
    def __init__(self, type, target, start=None, end=None):
        super(Reference, self).__init__(start=start, end=end)
        self.type = type
        self.target = target


class Definition(ChildNode):
    def __init__(self, type, source, signature, body, start=None, end=None):
        super(Definition, self).__init__(start=start, end=end)
        self.type = type
        self.source = source
        self.signature = signature
        self.body = body


class UnorderedList(ParentNode):
    pass


class OrderedList(ParentNode):
    pass


class ListItem(ParentNode):
    pass
