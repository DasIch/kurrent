# coding: utf-8
"""
    kurrent.writers
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from datetime import datetime
from itertools import count, repeat
from contextlib import contextmanager

import markupsafe

from kurrent import ast


class Writer(object):
    def __init__(self, stream):
        self.stream = stream

        self.indent_stack = []
        self.newlines = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if hasattr(self.stream, 'close'):
            self.stream.close()

    @contextmanager
    def indent(self, string):
        self.indent_stack.append(string)
        yield
        assert self.indent_stack.pop() == string

    def write(self, string):
        if self.newlines:
            for _ in range(self.newlines):
                self.stream.write(u'\n')
            self.stream.write(u''.join(self.indent_stack))
            self.newlines = 0
        self.stream.write(string)

    def newline(self):
        self.newlines += 1

    def write_line(self, string):
        self.write(string)
        self.newline()

    def write_lines(self, strings):
        for string in strings:
            self.write_line(string)

    def write_node(self, node):
        try:
            method = getattr(self, 'write_' + node.__class__.__name__)
        except AttributeError as error:
            error = error
            method = None
        if hasattr(node, 'children'):
            if method is None:
                self.write_children(node)
            else:
                result = method(node)
                if hasattr(result, '__enter__'):
                    with result as write_children:
                        if write_children:
                            self.write_children(node)
        else:
            if method is None:
                raise error
            method(node)

    def write_children(self, node):
        for child in node.children:
            self.write_node(child)


class KurrentWriter(Writer):
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
        self.write(node.text)

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

    def write_Reference(self, node):
        self.write(u'[')
        if node.target != node.text:
            self.write(node.text)
            self.write(u'][')
        if node.type is not None:
            self.write(node.type)
            self.write(u'|')
        self.write(node.target)
        self.write(u']')
        if node.definition is not None:
            self.write(u'(')
            self.write(node.definition)
            self.write(u')')

    def write_Definition(self, node):
        self.write(u'[')
        if node.type is not None:
            self.write(node.type)
            self.write(u'|')
        self.write(node.source)
        self.write(u']:')
        if node.signature:
            self.write(u' ')
            self.write(node.signature)
        with self.indent(u'  '):
            self.newline()
            self.write_lines(node.body)
        self.write_block_newline()

    @contextmanager
    def write_BlockQuote(self, node):
        self.write(u'> ')
        with self.indent(u'  '):
            yield True
        # block newline is emitted by last quoted block


class HTML5Writer(Writer):
    def write_Text(self, node):
        self.write(markupsafe.escape(node.text))

    @contextmanager
    def write_Paragraph(self, node):
        self.write(u'<p>')
        yield True
        self.write(u'</p>')

    def write_Header(self, node):
        self.write(u'<h%d>' % node.level)
        self.write(markupsafe.escape(node.text))
        self.write(u'</h%d>' % node.level)

    @contextmanager
    def write_UnorderedList(self, node):
        self.write(u'<ul>')
        yield True
        self.write(u'</ul>')

    @contextmanager
    def write_ListItem(self, node):
        self.write(u'<li>')
        yield True
        self.write(u'</li>')

    @contextmanager
    def write_Document(self, node):
        self.write(u'<!doctype html>')
        self.write(u'<title>%s</title>' % (
            node.metadata.get('title', u'')
        ))
        yield True

    @contextmanager
    def write_Emphasis(self, node):
        self.write(u'<em>')
        yield True
        self.write(u'</em>')

    @contextmanager
    def write_Strong(self, node):
        self.write(u'<strong>')
        yield True
        self.write(u'</strong>')

    def write_Reference(self, node):
        self.write(u'<a href="')
        self.write(node.definition)
        self.write(u'">')
        self.write(markupsafe.escape(node.text))
        self.write(u'</a>')

    def write_Definition(self, node):
        # prevents NotImplementedError, we ignore Definitions
        pass

    @contextmanager
    def write_BlockQuote(self, node):
        self.write(u'<blockquote>')
        yield True
        self.write(u'</blockquote>')


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
