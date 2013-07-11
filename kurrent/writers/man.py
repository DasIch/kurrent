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


class Indentation(ParentNode):
    def __init__(self, indentation, children=None):
        super(Indentation, self).__init__(children=children)
        self.indentation = indentation


class Translator(object):
    def translate(self, node):
        return getattr(self, 'translate_%s' % node.__class__.__name__)(node)

    def translate_children(self, node):
        rv = []
        for child in node.children:
            translated = self.translate(child)
            if hasattr(translated, '__iter__'):
                rv.extend(translated)
            else:
                rv.append(translated)
        return rv

    def translate_Document(self, node):
        return Document(
            title=node.metadata.get('title', u''),
            section=node.metadata.get('section', 1),
            date=datetime.now().strftime(u'%d %B %Y'),
            children=self.translate_children(node)
        )

    def translate_Header(self, node):
        if node.level == 1:
            return Section(node.text)
        elif node.level == 2:
            return SubSection(node.text)
        assert False, node.level

    def translate_Text(self, node):
        return Text(node.text)

    def translate_Emphasis(self, node):
        return Emphasis(children=self.translate_children(node))

    def translate_Strong(self, node):
        return Strong(children=self.translate_children(node))

    def translate_Paragraph(self, node):
        return Paragraph(children=self.translate_children(node))

    def translate_BlockQuote(self, node):
        return HangingIndentation(
            '>',
            designator=u'> ',
            indentation=2,
            children=self.translate_children(node)
        )

    def translate_OrderedList(self, node):
        indentation = len(u'%d. ' % len(node.children))
        for index, item in enumerate(node.children, start=1):
            yield HangingIndentation(
                'ol',
                designator=u'%d. ' % index,
                indentation=indentation,
                children=self.translate_children(item)
            )

    def translate_UnorderedList(self, node):
        for item in node.children:
            yield HangingIndentation(
                'ul',
                designator=u'\(bu ',
                indentation=2,
                children=self.translate_children(item)
            )


translate = Translator().translate


def fold(node):
    if isinstance(node, (Document, Indentation)):
        for child in node.children:
            if isinstance(child, HangingIndentation):
                child.nested = False
    elif isinstance(node, HangingIndentation):
        if node.children:
            if isinstance(node.children[0], HangingIndentation):
                child_indent = node.children.pop(0)
                if node.id != child_indent.id:
                    node.designator += child_indent.designator
                    node.children = (
                        child_indent.children +
                        [Indentation(
                            node.indentation,
                            node.children
                        )]
                    )
                    node.indentation += child_indent.indentation
            if isinstance(node.children[0], Paragraph):
                node.children[0].transparent = True
    if hasattr(node, 'children'):
        for child in node.children:
            fold(child)
    return node

def compile(node):
    nodes = translate(node)
    if not hasattr(nodes, '__iter__'):
        nodes = [nodes]
    for node in nodes:
        yield fold(node)


class ManWriter(Writer):
    @classmethod
    def get_file_extension(self, document):
        return '.%d' % document.metadata.get('section', 1)

    def write_node(self, kurrent_node):
        if isinstance(kurrent_node, ManASTNode):
            man_nodes = kurrent_node
        elif hasattr(kurrent_node, '__iter__'):
            man_nodes = kurrent_node
        else:
            man_nodes = compile(kurrent_node)
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

    @contextmanager
    def write_Indentation(self, node):
        self.write_line(u'.RS %d' % node.indentation)
        yield True
        self.write_line(u'.RE')
