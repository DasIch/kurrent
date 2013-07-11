# coding: utf-8
"""
    kurrent.writers.man
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from datetime import datetime
from contextlib import contextmanager

from .base import Writer


class ManASTNode(object):
    pass


class Text(ManASTNode):
    def __init__(self, text):
        self.text = text


class ParentNode(ManASTNode):
    def __init__(self, children=None):
        self.children = []

        if children is not None:
            self.add_children(children)

    def add_child(self, node):
        self.children.append(node)

    def add_children(self, nodes):
        for node in nodes:
            self.add_child(node)


class Document(ParentNode):
    def __init__(self, title=u'', section=u'', date=u'', author=u'',
                 children=None):
        super(Document, self).__init__(children=children)
        self.title = title
        self.section = section
        self.date = date
        self.author = author

    def add_child(self, node):
        if isinstance(node, HangingIndentation):
            node.nested = False
        super(Document, self).add_child(node)


class Section(ManASTNode):
    def __init__(self, title):
        self.title = title


class SubSection(ManASTNode):
    def __init__(self, title):
        self.title = title


class Paragraph(ParentNode):
    def __init__(self, transparent=False, children=None):
        super(Paragraph, self).__init__(children=children)
        self.transparent = transparent


class Emphasis(ParentNode):
    pass


class Strong(ParentNode):
    pass


class HangingIndentation(ParentNode):
    def __init__(self, id, designator=None, indentation=None, nested=True,
                 children=None):
        self.id = id
        self.designator = designator
        self.indentation = indentation
        self.nested = nested
        super(HangingIndentation, self).__init__(children=children)

    def add_child(self, node):
        if not self.children:
            if isinstance(node, Paragraph):
                node.transparent = True
                super(HangingIndentation, self).add_child(node)
                return
            elif isinstance(node, HangingIndentation) and self.id != node.id:
                self.designator += node.designator
                self.indentation += node.indentation
                self.add_children(node.children)
                return
        super(HangingIndentation, self).add_child(node)


class Compiler(object):
    def compile(self, node):
        return getattr(self, 'compile_%s' % node.__class__.__name__)(node)

    def compile_children(self, node):
        rv = []
        for child in node.children:
            compiled = self.compile(child)
            if hasattr(compiled, '__iter__'):
                rv.extend(compiled)
            else:
                rv.append(compiled)
        return rv

    def compile_Document(self, node):
        return Document(
            title=node.metadata.get('title', u''),
            section=node.metadata.get('section', 1),
            date=datetime.now().strftime(u'%d %B %Y'),
            children=self.compile_children(node)
        )

    def compile_Header(self, node):
        if node.level == 1:
            return Section(node.text)
        elif node.level == 2:
            return SubSection(node.text)
        assert False, node.level

    def compile_Text(self, node):
        return Text(node.text)

    def compile_Emphasis(self, node):
        return Emphasis(children=self.compile_children(node))

    def compile_Strong(self, node):
        return Strong(children=self.compile_children(node))

    def compile_Paragraph(self, node):
        return Paragraph(children=self.compile_children(node))

    def compile_BlockQuote(self, node):
        return HangingIndentation(
            '>',
            designator=u'> ',
            indentation=2,
            children=self.compile_children(node)
        )

    def compile_OrderedList(self, node):
        indentation = len(u'%d. ' % len(node.children))
        for index, item in enumerate(node.children, start=1):
            yield HangingIndentation(
                'ol',
                designator=u'%d. ' % index,
                indentation=indentation,
                children=self.compile_children(item)
            )

    def compile_UnorderedList(self, node):
        for item in node.children:
            yield HangingIndentation(
                'ul',
                designator=u'\(bu ',
                indentation=2,
                children=self.compile_children(item)
            )

compile_kurrent_ast = Compiler().compile


class ManWriter(Writer):
    def write_node(self, kurrent_node):
        if isinstance(kurrent_node, ManASTNode):
            man_nodes = kurrent_node
        elif hasattr(kurrent_node, '__iter__'):
            man_nodes = kurrent_node
        else:
            man_nodes = compile_kurrent_ast(kurrent_node)
        if not hasattr(man_nodes, '__iter__'):
            man_nodes = [man_nodes]
        for man_node in man_nodes:
            method = getattr(self, 'write_' + man_node.__class__.__name__)
            if hasattr(man_node, 'children'):
                result = method(man_node)
                if hasattr(result, '__enter__'):
                    with result as write_children:
                        if write_children:
                            self.write_children(man_node)
            else:
                method(man_node)

    def write_children(self, node):
        for child in node.children:
            self.write_node(child)

    def write_Text(self, node):
        self.write(node.text)

    @contextmanager
    def write_Emphasis(self, node):
        self.write(u'\\fI')
        yield True
        self.write(u'\\fP')

    @contextmanager
    def write_Strong(self, node):
        self.write(u'\\fB')
        yield True
        self.write(u'\\fP')

    @contextmanager
    def write_Paragraph(self, node):
        if not node.transparent:
            self.write_line(u'.P')
        yield True
        self.newline()

    def write_Section(self, node):
        self.write_line(u'.SH "%s"' % node.title)

    def write_SubSection(self, node):
        self.write_line(u'.SS "%s"' % node.title)

    @contextmanager
    def write_Document(self, node):
        self.write_line(u'.TH "%s" "%s" "%s" "%s"' % (
            node.title, node.section, node.date, node.author
        ))
        yield True

    @contextmanager
    def write_HangingIndentation(self, node):
        if node.nested:
            self.write_line(u'.RS')
        self.write_line(u'.IP "%s" %d' % (node.designator, node.indentation))
        yield True
        if node.nested:
            self.write_line(u'.RE')
