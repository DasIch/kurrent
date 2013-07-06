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
        document = ast.Document('<test>', children=[
            ast.Paragraph(children=[ast.Text(u'Hello')]),
            ast.Paragraph(children=[ast.Text(u'World')])
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
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'foo')])]),
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'bar')])])
        ])
        self.check_node(list, u'- foo\n'
                              u'- bar\n'
                              u'\n')

        list.add_child(ast.UnorderedList([
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'baz')])])
        ]))
        self.check_node(list, u'- foo\n'
                              u'- bar\n'
                              u'- - baz\n'
                              u'\n')

    def test_write_ordered_list(self):
        list = ast.OrderedList([
            ast.ListItem(children=[ast.Paragraph(children=[ast.Text(u'foo')])]),
            ast.ListItem(children=[ast.Paragraph(children=[ast.Text(u'bar')])])
        ])
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'\n')

        list.add_child(ast.OrderedList([
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'baz')])])
        ]))
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'3. 1. baz\n'
                              u'\n')

    def test_emphasis(self):
        emphasis = ast.Emphasis(children=[ast.Text(u'foo')])
        self.check_node(emphasis, u'*foo*')

    def test_strong(self):
        strong = ast.Strong(children=[ast.Text(u'foo')])
        self.check_node(strong, u'**foo**')

    def test_reference(self):
        reference = ast.Reference(None, u'foo', u'foo')
        self.check_node(reference, u'[foo]')

        reference = ast.Reference(u'foo', u'bar', u'bar')
        self.check_node(reference, u'[foo|bar]')

        reference = ast.Reference(None, u'foo', u'bar')
        self.check_node(reference, u'[bar][foo]')

        reference = ast.Reference(None, u'foo', u'foo', definition=u'bar')
        self.check_node(reference, u'[foo](bar)')

        reference = ast.Reference(u'foo', u'bar', u'bar', definition=u'baz')
        self.check_node(reference, u'[foo|bar](baz)')

        reference = ast.Reference(None, u'foo', u'bar', definition=u'baz')
        self.check_node(reference, u'[bar][foo](baz)')

        reference = ast.Reference(u'foo', u'bar', u'baz', definition=u'spam')
        self.check_node(reference, u'[baz][foo|bar](spam)')


class TestHTML5Writer(WriterTest):
    writer_cls = HTML5Writer

    def test_write_paragraph(self):
        self.check_node(
            ast.Paragraph(children=[ast.Text(u'foo')]),
            u'<p>foo</p>'
        )

        self.check_node(
            ast.Paragraph(children=[ast.Text(u'<p>')]),
            u'<p>&lt;p&gt;</p>'
        )

    def test_write_header(self):
        self.check_node(
            ast.Header(u'foo', 1),
            u'<h1>foo</h1>'
        )
        self.check_node(
            ast.Header(u'<p>', 1),
            u'<h1>&lt;p&gt;</h1>'
        )

    def test_write_unordered_list(self):
        list = ast.UnorderedList([
            ast.ListItem(children=[ast.Paragraph(children=[ast.Text(u'foo')])]),
            ast.ListItem(children=[ast.Paragraph(children=[ast.Text(u'bar')])])
        ])
        self.check_node(list, u'<ul><li><p>foo</p></li><li><p>bar</p></li></ul>')

    def test_write_document(self):
        document = ast.Document(
            '<test>',
            children=[ast.Paragraph(children=[ast.Text(u'foo')])]
        )
        self.check_node(document, u'<!doctype html><title></title><p>foo</p>')

        document = ast.Document('<test>', title=u'foo')
        self.check_node(document, u'<!doctype html><title>foo</title>')

    def test_write_emphasis(self):
        emphasis = ast.Emphasis(children=[ast.Text(u'foo')])
        self.check_node(emphasis, u'<em>foo</em>')

    def test_write_strong(self):
        strong = ast.Strong(children=[ast.Text(u'foo')])
        self.check_node(strong, u'<strong>foo</strong>')
