# coding: utf-8
"""
    kurrent.writers
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from itertools import count
from contextlib import contextmanager

import markupsafe


class Writer(object):
    def __init__(self, stream):
        self.stream = stream

        self.new_indent_stack = []
        self.indent_stack = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if hasattr(self.stream, 'close'):
            self.stream.close()

    @contextmanager
    def indent(self, string):
        self.new_indent_stack.append(string)
        yield
        assert self.indent_stack.pop() == string

    def write(self, string):
        self.stream.write(u''.join(self.indent_stack))
        self.stream.write(string)

    def newline(self):
        self.indent_stack.extend(self.new_indent_stack)
        del self.new_indent_stack[:]
        self.stream.write(u'\n')

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
        self.write(u'%s %s' % (u'#' * node.level, node.text))
        self.newline()
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
            for line in node.body:
                self.write(line)
                self.newline()
        self.write_block_newline()


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
            u'' if node.title is None else node.title
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
