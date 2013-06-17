# coding: utf-8
"""
    tests.test_writers
    ~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from io import StringIO

from kurrent import ast
from kurrent.writers import KurrentWriter, HTML5Writer


class WriterTest(object):
    writer_cls = None

    def check_node(self, node, result):
        __tracebackhide__ = True
        stream = StringIO()
        self.writer_cls(stream).write_node(node)
        assert stream.getvalue() == result


class TestKurrentWriter(WriterTest):
    writer_cls = KurrentWriter

    def test_write_paragraph(self):
        document = ast.Document('<test>')
        document.children.extend([
            ast.Paragraph(u'Hello'),
            ast.Paragraph(u'World')
        ])
        self.check_node(document, u'Hello\n'
                                  u'\n'
                                  u'World\n'
                                  u'\n')

    def test_write_header(self):
        self.check_node(ast.Header(u'Hello World', 1),
                        u'# Hello World\n'
                        u'\n')

    def test_write_unordered_list(self):
        list = ast.UnorderedList([
            ast.ListItem([ast.Paragraph(u'foo')]),
            ast.ListItem([ast.Paragraph(u'bar')])
        ])
        self.check_node(list, u'* foo\n'
                              u'* bar\n'
                              u'\n')

        list.children.append(ast.UnorderedList([
            ast.ListItem([ast.Paragraph(u'baz')])
        ]))
        self.check_node(list, u'* foo\n'
                              u'* bar\n'
                              u'* * baz\n'
                              u'\n')

    def test_write_ordered_list(self):
        list = ast.OrderedList([
            ast.ListItem([ast.Paragraph(u'foo')]),
            ast.ListItem([ast.Paragraph(u'bar')])
        ])
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'\n')

        list.children.append(ast.OrderedList([
            ast.ListItem([ast.Paragraph(u'baz')])
        ]))
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'3. 1. baz\n'
                              u'\n')


class TestHTML5Writer(WriterTest):
    writer_cls = HTML5Writer

    def test_write_paragraph(self):
        self.check_node(ast.Paragraph(u'foo'), u'<p>foo</p>')

        self.check_node(ast.Paragraph(u'<p>'), u'<p>&lt;p&gt;</p>')

    def test_write_header(self):
        self.check_node(ast.Header(u'foo', 1), u'<h1>foo</h1>')
        self.check_node(ast.Header(u'<p>', 1), u'<h1>&lt;p&gt;</h1>')

    def test_write_unordered_list(self):
        list = ast.UnorderedList([
            ast.ListItem([ast.Paragraph(u'foo')]),
            ast.ListItem([ast.Paragraph(u'bar')])
        ])
        self.check_node(list, u'<ul><li><p>foo</p></li><li><p>bar</p></li></ul>')

    def test_write_document(self):
        document = ast.Document('<test>', children=[ast.Paragraph(u'foo')])
        self.check_node(document, u'<!doctype html><title></title><p>foo</p>')

        document = ast.Document('<test>', title=u'foo')
        self.check_node(document, u'<!doctype html><title>foo</title>')
