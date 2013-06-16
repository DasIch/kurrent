# coding: utf-8
"""
    kurrent.writers
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from itertools import count
from contextlib import contextmanager


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
        method = getattr(self, 'write_' + node.__class__.__name__, None)
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

    def write_Paragraph(self, node):
        self.write(node.text)
        self.newline()
        self.write_block_newline()

    def write_Header(self, node):
        self.write(u'%s %s' % (u'#' * node.level, node.text))
        self.newline()
        self.write_block_newline()

    def write_UnorderedList(self, node):
        writer = self._write_list(node)
        next(writer)
        while True:
            try:
                writer.send(u'* ')
            except StopIteration:
                break

    def write_OrderedList(self, node):
        writer = self._write_list(node)
        next(writer)
        for index in count(start=1):
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
