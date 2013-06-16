# coding: utf-8
"""
    test_kurrent
    ~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from io import StringIO

from kurrent import ast
from kurrent.parser import Parser, LineIterator
from kurrent.writers import KurrentWriter

import pytest


class TestLineIterator(object):
    def test_next(self):
        iterator = LineIterator([u'foo', u'bar\n', u'baz\r', u'spam\r\n'])
        assert list(iterator) == [u'foo', u'bar', u'baz', u'spam']

    def test_next_block(self):
        iterator = LineIterator([u'foobar'])
        assert iterator.next_block() == [u'foobar']

        iterator = LineIterator([u'foo', u'bar'])
        assert iterator.next_block() == [u'foo', u'bar']

        iterator = LineIterator([u'foo', u'', u'bar'])
        assert iterator.next_block() == [u'foo']
        assert iterator.next_block() == [u'bar']

        iterator = LineIterator([u'foo', u'', u'', u'bar'])
        assert iterator.next_block() == [u'foo']
        assert iterator.next_block() == [u'bar']

        iterator = LineIterator([u'foo', u'', u' bar'])
        assert iterator.next_block() == [u'foo', u'', u' bar']


class TestParagraph(object):
    def test_single_line(self):
        document = Parser.from_string(u'foobar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == u'foobar'

    def test_muliple_lines(self):
        document = Parser.from_string(u'foo\nbar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == u'foo bar'

    def test_multiple_paragraphs(self):
        document = Parser.from_string(u'foo\n\nbar').parse()
        assert len(document.children) == 2
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == u'foo'
        assert isinstance(document.children[1], ast.Paragraph)
        assert document.children[1].text == u'bar'


@pytest.mark.parametrize(('string', 'text', 'level'), [
    (u'# Hello', u'Hello', 1),
    (u'## Hello', u'Hello', 2)
])
def test_header(string, text, level):
    document = Parser.from_string(string).parse()
    assert len(document.children) == 1
    assert isinstance(document.children[0], ast.Header)
    assert document.children[0].text == text
    assert document.children[0].level == level


class TestUnorderedList(object):
    def test_not_a_list(self):
        document = Parser.from_string(u'* this paragraph begins with an\n'
                                      u'asterisk, it\'s not a list\n'
                                      u'though.').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == (u'* this paragraph begins with '
                                             u'an asterisk, it\'s not a list '
                                             u'though.')

    def test_simple(self):
        document = Parser.from_string(u'* foo\n'
                                      u'* bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.UnorderedList)
        list = document.children[0]
        assert len(list.children) == 2
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(list.children[i], ast.ListItem)
            item = list.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            assert item.children[0].text == text

    def test_multiple_line_items(self):
        document = Parser.from_string(u'* foo\n'
                                      u'  bar\n'
                                      u'* baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.UnorderedList)
        list = document.children[0]
        assert len(list.children) == 2
        for i, text in enumerate([u'foo bar', u'baz']):
            assert isinstance(list.children[i], ast.ListItem)
            item = list.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            assert item.children[0].text == text

    def test_bad_multiple_line_items(self):
        document = Parser.from_string(u'* foo\n'
                                      u' bar\n'
                                      u'* baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == u'* foo  bar * baz'

    def test_nested(self):
        document = Parser.from_string(u'* * foo\n'
                                      u'  * bar\n'
                                      u'  * * baz\n'
                                      u'* baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.UnorderedList)
        list = document.children[0]
        assert len(list.children) == 2

        assert isinstance(list.children[0], ast.ListItem)
        item = list.children[0]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.UnorderedList)
        nested = item.children[0]
        assert len(nested.children) == 3
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(nested.children[i], ast.ListItem)
            item = nested.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            assert item.children[0].text == text

        assert isinstance(nested.children[2], ast.ListItem)
        item = nested.children[2]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.UnorderedList)
        double_nested = item.children[0]
        assert len(double_nested.children) == 1
        item = double_nested.children[0]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        assert item.children[0].text == u'baz'

        assert isinstance(list.children[1], ast.ListItem)
        item = list.children[1]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        assert item.children[0].text == u'baz'

    def test_multiple_block_items(self):
        document = Parser.from_string(u'* foo\n'
                                      u'\n'
                                      u'  bar\n').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.UnorderedList)
        list = document.children[0]
        assert len(list.children) == 1
        assert isinstance(list.children[0], ast.ListItem)
        item = list.children[0]
        assert len(item.children) == 2
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(item.children[i], ast.Paragraph)
            assert item.children[i].text == text


class TestOrderedList(object):
    def test_not_a_list(self):
        document = Parser.from_string(u'1. this paragraph begins with a\n'
                                      u'number, it\'s not a list\n'
                                      u'though.').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == (u'1. this paragraph begins with '
                                             u'a number, it\'s not a list '
                                             u'though.')

    def test_simple(self):
        document = Parser.from_string(u'1. foo\n'
                                      u'2. bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.OrderedList)
        list = document.children[0]
        assert len(list.children) == 2
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(list.children[i], ast.ListItem)
            item = list.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            assert item.children[0].text == text

    def test_multiple_line_items(self):
        document = Parser.from_string(u'1. foo\n'
                                      u'   bar\n'
                                      u'2. baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.OrderedList)
        list = document.children[0]
        assert len(list.children) == 2
        for i, text in enumerate([u'foo bar', u'baz']):
            assert isinstance(list.children[i], ast.ListItem)
            item = list.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            assert item.children[0].text == text

    def test_bad_multiple_line_items(self):
        document = Parser.from_string(u'1. foo\n'
                                      u'  bar\n'
                                      u'2. baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        assert document.children[0].text == u'1. foo   bar 2. baz'

    def test_nested(self):
        document = Parser.from_string(u'1. 1. foo\n'
                                      u'   2. bar\n'
                                      u'   2. 3. baz\n'
                                      u'2. baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.OrderedList)
        list = document.children[0]
        assert len(list.children) == 2

        assert isinstance(list.children[0], ast.ListItem)
        item = list.children[0]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.OrderedList)
        nested = item.children[0]
        assert len(nested.children) == 3
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(nested.children[i], ast.ListItem)
            item = nested.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            assert item.children[0].text == text

        assert isinstance(nested.children[2], ast.ListItem)
        item = nested.children[2]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.OrderedList)
        double_nested = item.children[0]
        assert len(double_nested.children) == 1
        item = double_nested.children[0]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        assert item.children[0].text == u'baz'

        assert isinstance(list.children[1], ast.ListItem)
        item = list.children[1]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        assert item.children[0].text == u'baz'

    def test_multiple_block_items(self):
        document = Parser.from_string(u'1. foo\n'
                                      u'\n'
                                      u'   bar\n').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.OrderedList)
        list = document.children[0]
        assert len(list.children) == 1
        assert isinstance(list.children[0], ast.ListItem)
        item = list.children[0]
        assert len(item.children) == 2
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(item.children[i], ast.Paragraph)
            assert item.children[i].text == text


class TestKurrentWriter(object):
    def check_node(self, node, result):
        __tracebackhide__ = True
        stream = StringIO()
        KurrentWriter(stream).write_node(node)
        assert stream.getvalue() == result

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
        list = ast.UnorderedList()
        item = ast.ListItem()
        item.children.append(ast.Paragraph(u'foo'))
        list.children.append(item)
        item = ast.ListItem()
        item.children.append(ast.Paragraph(u'bar'))
        list.children.append(item)
        self.check_node(list, u'* foo\n'
                              u'* bar\n'
                              u'\n')

        nested = ast.UnorderedList()
        item = ast.ListItem()
        item.children.append(ast.Paragraph(u'baz'))
        nested.children.append(item)
        list.children.append(nested)
        self.check_node(list, u'* foo\n'
                              u'* bar\n'
                              u'* * baz\n'
                              u'\n')

    def test_write_ordered_list(self):
        list = ast.OrderedList()
        item = ast.ListItem()
        item.children.append(ast.Paragraph(u'foo'))
        list.children.append(item)
        item = ast.ListItem()
        item.children.append(ast.Paragraph(u'bar'))
        list.children.append(item)
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'\n')

        nested = ast.OrderedList()
        item = ast.ListItem()
        item.children.append(ast.Paragraph(u'baz'))
        nested.children.append(item)
        list.children.append(nested)
        self.check_node(list, u'1. foo\n'
                              u'2. bar\n'
                              u'3. 1. baz\n'
                              u'\n')
