# coding: utf-8
"""
    kurrent.writers.man
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from datetime import datetime
from itertools import repeat

from contextlib import contextmanager

from .. import ast
from .base import Writer


class ManWriter(Writer):
    def __init__(self, *args, **kwargs):
        super(ManWriter, self).__init__(*args, **kwargs)

        self.indented = False

    @contextmanager
    def write_Document(self, node):
        self.write_line(u'.TH "{title}" "{section}" "{date}" "{author}"'.format(
            title=node.metadata.get('title', u''),
            section=1,
            date=datetime.now().strftime(u'%d %B %Y'),
            author=u''
        ))
        yield True

    def write_Header(self, node):
        if node.level == 1:
            macro = u'SH'
        else:
            macro = u'SS'
        self.write_line(u'.{macro} "{text}"'.format(macro=macro, text=node.text))

    @contextmanager
    def write_Paragraph(self, node):
        self.write_line(u'.sp')
        yield True
        self.newline()

    def write_Text(self, node):
        self.write(node.text)

    def write_UnorderedList(self, node):
        self._write_list(zip(repeat(u'\(bu'), repeat(1), node.children))

    def write_OrderedList(self, node):
        designators = [u'%d.' % i for i in range(1, len(node.children) + 1)]
        designator_lengths = map(len, designators)
        self._write_list(zip(designators, designator_lengths, node.children))

    def _write_list(self, items):
        items = list(items)
        longest_designator = max(
            designator_length for _, designator_length, _ in items
        )
        indentation = longest_designator + 1
        for designator, _, item in items:
            self._write_list_item(designator, indentation, item)

    @contextmanager
    def hanging_indent(self, string, indentation):
        old_indented = self.indented
        if self.indented:
            self.write_line(u'.RS')
        else:
            self.write_line(u'.RS 0')
            self.indented = True
        self.write_line(u'.IP {string} {indentation}'.format(
            string=string,
            indentation=indentation
        ))
        yield
        self.write_line(u'.in -%d' % indentation)
        self.write_line(u'.RE')
        self.indented = old_indented

    def _write_list_item(self, designator, indentation, node):
        with self.hanging_indent(designator, indentation):
            if node.children:
                # If we do an .sp as first item we get a newline directly after
                # the bullet point so we skip that.
                if isinstance(node.children[0], ast.Paragraph):
                    for grandchildren in node.children[0].children:
                        self.write_node(grandchildren)
                    self.newline()
                for child in node.children[1:]:
                    self.write_node(child)

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

    def write_BlockQuote(self, node):
        with self.hanging_indent(u'> ', 2):
            if node.children:
                # If we do an .sp as first item we get a newline directly after
                # the angle bracket so we skip that.
                if isinstance(node.children[0], ast.Paragraph):
                    for grandchildren in node.children[0].children:
                        self.write_node(grandchildren)
                    self.newline()
                    children = node.children[1:]
                else:
                    children = node.children
                for child in children:
                    self.write_node(child)
