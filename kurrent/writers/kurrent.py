# coding: utf-8
"""
    kurrent.writers.kurrent
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from itertools import count
from contextlib import contextmanager

from ..utils import StringBuilder
from .base import Writer


def escape(string):
    builder = StringBuilder(size=len(string))
    for char in string:
        builder.append({
            u'*': u'\*',
            u'[': u'\[',
            u']': u'\]'
        }.get(char, char))
    return builder.build()


class KurrentWriter(Writer):
    @classmethod
    def get_file_extension(self, document):
        return '.kr'

    def __init__(self, stream):
        super(KurrentWriter, self).__init__(stream)

        self.post_block_newline = True

    def write_block_newline(self):
        if self.post_block_newline:
            self.newline()

    @contextmanager
    def no_post_block_newline(self):
        old_post_block_newline = self.post_block_newline
        self.post_block_newline = False
        yield
        self.post_block_newline = old_post_block_newline

    @contextmanager
    def write_Paragraph(self, node):
        yield True
        self.newline()
        self.write_block_newline()

    def write_Header(self, node):
        self.write_line(u'%s %s' % (u'#' * node.level, node.text))
        self.write_block_newline()

    def write_Text(self, node):
        self.write(escape(node.text))

    def write_UnorderedList(self, node):
        writer = self._write_list(node)
        next(writer)
        while True:
            try:
                writer.send(u'- ')
            except StopIteration:
                break

    def write_OrderedList(self, node):
        writer = self._write_list(node)
        next(writer)
        for index in count(1):
            try:
                writer.send(u'%d. ' % index)
            except StopIteration:
                break

    def _write_list(self, node):
        with self.no_post_block_newline():
            for child in node.children:
                label = yield
                self.write(label)
                with self.indent(u' ' * len(label)):
                    self.write_node(child)
        self.write_block_newline()

    @contextmanager
    def write_Emphasis(self, node):
        self.write(u'*')
        yield True
        self.write(u'*')

    @contextmanager
    def write_Strong(self, node):
        self.write(u'**')
        yield True
        self.write(u'**')

    def write_InlineExtension(self, node):
        self.write(u'[')
        if node.text is not None:
            self.write(node.text)
            self.write(u'][')
        if node.type is not None:
            self.write(node.type)
            self.write(u'|')
        self.write(node.primary)
        self.write(u']')
        if node.secondary is not None:
            self.write(u'(')
            self.write(node.secondary)
            self.write(u')')

    def write_Extension(self, node):
        self.write(u'[')
        if node.type is not None:
            self.write(node.type)
            self.write(u'|')
        self.write(node.primary)
        self.write(u']:')
        if node.secondary is not None:
            self.write(u' ')
            self.write(node.secondary)
        self.newline()
        with self.indent(u' ' * 4):
            self.write_lines(node.body)

    @contextmanager
    def write_BlockQuote(self, node):
        self.write(u'> ')
        with self.indent(u'  '):
            yield True
        # block newline is emitted by last quoted block

    @contextmanager
    def write_RawBlock(self, node):
        for line in node.body:
            self.write_line(u' ' * 4 + line)
        self.write_block_newline()

    def write_Definition(self, node):
        for child in node.term:
            self.write_node(child)
        self.newline()
        with self.indent(u' ' * 2):
            for child in node.description:
                self.write_node(child)
