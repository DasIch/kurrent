# coding: utf-8
"""
    kurrent.writers.base
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from contextlib import contextmanager


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

