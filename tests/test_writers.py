# coding: utf-8
"""
    tests.test_writers
    ~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import re
import codecs
import subprocess
from io import StringIO

import pytest

from kurrent import ast
from kurrent.writers import KurrentWriter, HTML5Writer, ManWriter


class WriterTest(object):
    writer_cls = None

    def render_node(self, node):
        stream = StringIO()
        self.writer_cls(stream).write_node(node)
        return stream.getvalue()

    def check_node(self, node, result):
        __tracebackhide__ = True
        assert self.render_node(node) == result

    def match_node(self, node, regex):
        __tracebackhide__ = True
        assert re.match(regex, self.render_node(node)) is not None


class TestKurrentWriter(WriterTest):
    writer_cls = KurrentWriter

    def test_get_file_extensions(self):
        document = ast.Document(u'<test>')
        assert KurrentWriter.get_file_extension(document) == '.kr'

    def test_write_text(self):
        self.check_node(ast.Text(u'foo'), u'foo')
        self.check_node(ast.Text(u'*'), u'\*')
        self.check_node(ast.Text(u'[foo]'), u'\[foo\]')

    def test_write_paragraph(self):
        document = ast.Document('<test>', children=[
            ast.Paragraph(children=[ast.Text(u'Hello')]),
            ast.Paragraph(children=[ast.Text(u'World')])
        ])
        self.check_node(document, u'Hello\n'
                                  u'\n'
                                  u'World')

    def test_write_header(self):
        self.check_node(ast.Header(u'Hello World', 1),
                        u'# Hello World')

    def test_write_unordered_list(self):
        list = ast.UnorderedList([
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'foo')])]),
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'bar')])])
        ])
        self.check_node(list, u'- foo\n'
                              u'- bar')

        list.add_child(ast.UnorderedList([
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'baz')])])
        ]))
        self.check_node(list, u'- foo\n'
                              u'- bar\n'
                              u'- - baz')

    def test_write_ordered_list(self):
        list = ast.OrderedList([
            ast.ListItem(children=[ast.Paragraph(children=[ast.Text(u'foo')])]),
            ast.ListItem(children=[ast.Paragraph(children=[ast.Text(u'bar')])])
        ])
        self.check_node(list, u'1. foo\n'
                              u'2. bar')

        list.add_child(ast.OrderedList([
            ast.ListItem([ast.Paragraph(children=[ast.Text(u'baz')])])
        ]))
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'3. 1. baz')

    def test_emphasis(self):
        emphasis = ast.Emphasis(children=[ast.Text(u'foo')])
        self.check_node(emphasis, u'*foo*')

    def test_strong(self):
        strong = ast.Strong(children=[ast.Text(u'foo')])
        self.check_node(strong, u'**foo**')

    def test_block_quote(self):
        block_quote = ast.BlockQuote(children=[
            ast.Paragraph(children=[
                ast.Text(u'foo')
            ])
        ])
        self.check_node(block_quote, u'> foo')

        block_quote.add_child(ast.BlockQuote(children=[
            ast.Paragraph(children=[
                ast.Text(u'bar')
            ])
        ]))
        self.check_node(
            block_quote,
            u'> foo\n'
            u'\n'
            u'  > bar'
        )

    def test_write_raw_block(self):
        raw_block = ast.RawBlock([
            u'foo',
            u'bar'
        ])
        self.check_node(
            raw_block,
            u'    foo\n'
            u'    bar'
        )


class TestHTML5Writer(WriterTest):
    writer_cls = HTML5Writer

    def test_get_file_extension(self):
        document = ast.Document('<test>')
        assert HTML5Writer.get_file_extension(document) == '.html'

    def test_write_paragraph(self):
        self.check_node(
            ast.Paragraph(children=[ast.Text(u'foo')]),
            u'<p>\n'
            u'  foo\n'
            u'</p>'
        )

        self.check_node(
            ast.Paragraph(children=[ast.Text(u'<p>')]),
            u'<p>\n'
            u'  &lt;p&gt;\n'
            u'</p>'
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
        self.check_node(list,
            u'<ul>\n'
            u'  <li>\n'
            u'    <p>\n'
            u'      foo\n'
            u'    </p>\n'
            u'  </li>\n'
            u'  <li>\n'
            u'    <p>\n'
            u'      bar\n'
            u'    </p>\n'
            u'  </li>\n'
            u'</ul>'
        )

    def test_write_document(self):
        document = ast.Document(
            '<test>',
            children=[ast.Paragraph(children=[ast.Text(u'foo')])]
        )
        self.check_node(document,
            u'<!doctype html>\n'
            u'<title></title>\n'
            u'<p>\n'
            u'  foo\n'
            u'</p>'
        )

        document = ast.Document('<test>', metadata={'title': u'foo<'})
        self.check_node(document,
            u'<!doctype html>\n'
            u'<title>foo&lt;</title>'
        )

    def test_write_emphasis(self):
        emphasis = ast.Emphasis(children=[ast.Text(u'foo')])
        self.check_node(emphasis, u'<em>foo</em>')

    def test_write_strong(self):
        strong = ast.Strong(children=[ast.Text(u'foo')])
        self.check_node(strong, u'<strong>foo</strong>')

    def test_write_block_quote(self):
        block_quote = ast.BlockQuote(children=[
            ast.Paragraph(children=[
                ast.Text(u'foo')
            ])
        ])
        self.check_node(block_quote,
            u'<blockquote>\n'
            u'  <p>\n'
            u'    foo\n'
            u'  </p>\n'
            u'</blockquote>'
        )

    def test_write_raw_block(self):
        raw_block = ast.RawBlock([
            u'foo\n'
            u'bar'
        ])
        self.check_node(raw_block,
            u'<pre>\n'
            u'foo\n'
            u'bar\n'
            u'</pre>'
        )


class TestManWriter(WriterTest):
    writer_cls = ManWriter

    @pytest.fixture
    def document_sample(self):
        return ast.Document('<test>', metadata={'title': u'foo'}, children=[
            ast.Paragraph(children=[
                ast.Text(u'some regular text'),
                ast.Emphasis(children=[
                    ast.Text(u'something emphasized')
                ]),
                ast.Strong(children=[
                    ast.Text(u'something strongly emphasized')
                ])
            ]),
            ast.UnorderedList(children=[
                ast.ListItem(children=[
                    ast.Paragraph(children=[
                        ast.Text(u'a list item')
                    ]),
                    ast.Paragraph(children=[
                        ast.Text(u'with two paragraphs')
                    ])
                ]),
                ast.ListItem(children=[
                    ast.Paragraph(children=[
                        ast.Text(u'another list item')
                    ])
                ])
            ]),
            ast.OrderedList(children=[
                ast.ListItem(children=[
                    ast.Paragraph(children=[
                        ast.Text(u'a list item in an ordered list')
                    ])
                ])
            ])
        ])

    @pytest.fixture
    def document_sample_path(self, document_sample, temp_file_path):
        with codecs.open(temp_file_path, 'w', encoding=u'utf-8') as file:
            file.write(self.render_node(document_sample))
        return temp_file_path

    @pytest.fixture(params=['troff', 'nroff', 'groff'])
    def roff_implementation(self, request):
        return request.param

    def test_compileable(self, roff_implementation, document_sample_path):
        try:
            process = subprocess.Popen(
                [roff_implementation, '-man', document_sample_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except OSError:
            pytest.skip(u'%s missing' % roff_implementation)
        stdout, stderr = process.communicate()
        assert process.returncode == 0
        assert stderr == b''
        assert stdout

    def test_get_file_extension(self):
        document = ast.Document('<test>')
        assert ManWriter.get_file_extension(document) == u'.1'

        document.metadata['section'] = 1
        assert ManWriter.get_file_extension(document) == u'.1'

        document.metadata['section'] = 2
        assert ManWriter.get_file_extension(document) == u'.2'

    def test_document(self):
        document = ast.Document('<test>', metadata={'title': u'foo'})
        self.match_node(document, u'.TH "foo" "1" "\d{2} \w+ \d{4}" ""')

    def test_header(self):
        header = ast.Header(u'foo', 1)
        self.check_node(header, u'.SH "foo"')

        header = ast.Header(u'foo', 2)
        self.check_node(header, u'.SS "foo"')

    def test_paragraph(self):
        paragraph = ast.Paragraph(children=[ast.Text(u'foo')])
        self.check_node(paragraph, u'.P\nfoo')

    def test_unordered_list(self):
        list = ast.UnorderedList(children=[
            ast.ListItem(children=[ast.Paragraph(children=[
                ast.Text(u'foo')
            ])]),
            ast.ListItem(children=[
                ast.Paragraph(children=[
                    ast.Text(u'bar')
                ]),
                ast.Paragraph(children=[
                    ast.Text(u'baz')
                ])
            ])
        ])
        self.check_node(
            list,
            u'.RS\n'
            u'.IP "\(bu " 2\n'
            u'foo\n'
            u'.RE\n'
            u'.RS\n'
            u'.IP "\(bu " 2\n'
            u'bar\n'
            u'.P\n'
            u'baz\n'
            u'.RE'
        )

    def test_ordered_list(self):
        list = ast.OrderedList(children=[ast.ListItem(children=[
            ast.Paragraph(children=[ast.Text(u'foo')])
        ])])
        self.check_node(
            list,
            u'.RS\n'
            u'.IP "1. " 3\n'
            u'foo\n'
            u'.RE'
        )

        list = ast.OrderedList()
        for _ in range(10):
            list.add_child(ast.ListItem(children=[
                ast.Paragraph(children=[ast.Text(u'foo')])
            ]))
        item = (
            u'.RS\n'
            u'.IP "%s. " 4\n'
            u'foo\n'
            u'.RE\n'
        )
        self.check_node(
            list,
            u''.join(item % i for i in range(1, 11)).strip()
        )

    def test_emphasis(self):
        emphasis = ast.Emphasis(children=[ast.Text(u'foo')])
        self.check_node(emphasis, u'\\fIfoo\\fP')

        p = ast.Paragraph(children=[emphasis, ast.Text(u'bar')])
        self.check_node(p, u'.P\n\\fIfoo\\fPbar')

    def test_strong(self):
        strong = ast.Strong(children=[ast.Text(u'foo')])
        self.check_node(strong, u'\\fBfoo\\fP')

        p = ast.Paragraph(children=[strong, ast.Text(u'bar')])
        self.check_node(p, u'.P\n\\fBfoo\\fPbar')

    def test_block_quote(self):
        b = ast.BlockQuote(children=[
            ast.Paragraph(children=[
                ast.Text(u'foo')
            ])
        ])
        self.check_node(b,
            u'.RS\n'
            u'.IP "> " 2\n'
            u'foo\n'
            u'.RE'
        )

        b = ast.BlockQuote(children=[
            ast.OrderedList(children=[
                ast.ListItem(children=[
                    ast.Paragraph(children=[ast.Text(u'foo')])
                ]),
                ast.ListItem(children=[
                    ast.Paragraph(children=[ast.Text(u'bar')])
                ])
            ])
        ])
        self.check_node(b,
            u'.RS\n'
            u'.IP "> 1. " 5\n'
            u'foo\n'
            u'.RS 2\n'
            u'.IP "2. " 3\n'
            u'bar\n'
            u'.RE\n'
            u'.RE'
        )
