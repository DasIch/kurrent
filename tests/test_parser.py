# coding: utf-8
"""
    tests.test_parser
    ~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest

from kurrent import ast
from kurrent.parser import LineIterator, Parser, DocumentError


class TestParser(object):
    def test_from_bytes(self):
        parser = Parser.from_bytes(u'äöü'.encode('latin-1'))
        with pytest.raises(DocumentError):
            parser.parse()


class TestLineIterator(object):
    def test_next(self):
        iterator = LineIterator([u'foo', u'bar\n', u'baz\r', u'spam\r\n'])
        for lineno, content in enumerate([u'foo', u'bar', u'baz', u'spam'], 1):
            line = next(iterator)
            assert line == content
            assert line.lineno == lineno
            assert line.columnno == 1

    def test_push(self):
        iterator = LineIterator([u'foo'])
        line = next(iterator)
        assert iterator.lineno == 1
        assert line == u'foo'
        iterator.push(u'bar')
        line = next(iterator)
        assert iterator.lineno == 1
        assert line == u'bar'

    def test_until(self):
        iterator = LineIterator([u'foo', u'bar', u'baz']).until(lambda l: l == u'baz')
        for lineno, content in enumerate([u'foo', u'bar'], 1):
            line = next(iterator)
            assert line == content
            assert line.start == ast.Location(lineno, 1)
            assert line.end == ast.Location(lineno, 4)
        assert list(iterator) == []

    def test_unindented(self):
        iterator = LineIterator([u'  foo', u'  bar', u'  baz']).unindented(2)
        for lineno, content in enumerate([u'foo', u'bar', u'baz'], 1):
            line = next(iterator)
            assert line == content
            assert line.start == ast.Location(lineno, 3)
            assert line.end == ast.Location(lineno, 6)

        iterator = LineIterator([u'foo'])
        assert list(iterator.unindented(2)) == []

        iterator = LineIterator([u'  foo', u'  bar', u' baz'])
        assert list(iterator.unindented(2)) == [u'foo', u'bar']


class TestParagraph(object):
    def test_single_line(self):
        document = Parser.from_string(u'foobar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert p.start == ast.Location(1, 1)
        assert p.end == ast.Location(1, 7)
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foobar'

    def test_muliple_lines(self):
        document = Parser.from_string(u'foo\nbar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert p.start == ast.Location(1, 1)
        assert p.end == ast.Location(2, 4)
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo bar'

    def test_multiple_paragraphs(self):
        document = Parser.from_string(u'foo\n\nbar').parse()
        assert len(document.children) == 2
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert p.start == ast.Location(1, 1)
        assert p.end == ast.Location(1, 4)
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo'
        assert isinstance(document.children[1], ast.Paragraph)
        p = document.children[1]
        assert p.start == ast.Location(3, 1)
        assert p.end == ast.Location(3, 4)
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'bar'


class InlineMarkupTest(object):
    def test_only(self, node_cls, markup_string):
        code = markup_string % u'foo'
        document = Parser.from_string(code).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], node_cls)
        m = p.children[0]
        assert len(m.children) == 1
        assert m.start == ast.Location(1, 1)
        assert m.end == ast.Location(1, len(code) + 1)
        assert isinstance(m.children[0], ast.Text)
        assert m.children[0].text == u'foo'

    def test_multiple_lines(self, node_cls, markup_string):
        code = markup_string % u'foo\nbar'
        document = Parser.from_string(code).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], node_cls)
        m = p.children[0]
        assert len(m.children) == 1
        assert isinstance(m.children[0], ast.Text)

    def test_followed_by_text(self, node_cls, markup_string):
        code = (markup_string % u'foo') + u'bar'
        document = Parser.from_string(code).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], node_cls)
        e = p.children[0]
        assert e.start == ast.Location(1, 1)
        assert e.end == ast.Location(1, len(code) + 1 - len(u'bar'))
        assert len(e.children) == 1
        assert isinstance(e.children[0], ast.Text)
        assert e.children[0].text == u'foo'

    def test_preceded_by_text(self, node_cls, markup_string):
        code = u'foo' + (markup_string % u'bar')
        document = Parser.from_string(code).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo'
        assert isinstance(p.children[1], node_cls)
        e = p.children[1]
        assert len(e.children) == 1
        assert e.start == ast.Location(1, 4)
        assert e.end == ast.Location(1, len(code) + 1)
        assert e.children[0].text == u'bar'

    def test_surrounded_by_text(self, node_cls, markup_string):
        code = u'foo' + (markup_string % u'bar') + u'baz'
        document = Parser.from_string(code).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 3
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo'
        assert p.children[0].start == ast.Location(1, 1)
        assert p.children[0].end == ast.Location(1, len(u'foo') + 1)
        assert isinstance(p.children[1], node_cls)
        m = p.children[1]
        assert len(m.children) == 1
        assert m.start == ast.Location(1, len(u'foo') + 1)
        assert m.end == ast.Location(1, len(code) + 1 - len(u'baz'))
        assert isinstance(m.children[0], ast.Text)
        assert m.children[0].text == u'bar'
        assert isinstance(p.children[2], ast.Text)
        assert p.children[2].text == u'baz'
        assert p.children[2].start == ast.Location(1, len(code) + 1 - len(u'baz'))
        assert p.children[2].end == ast.Location(1, len(code) + 1)

    def test_surrounding_text(self, node_cls, markup_string):
        code = (markup_string % u'foo') + u'bar' + (markup_string % u'baz')
        document = Parser.from_string(code).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 3
        assert isinstance(p.children[0], node_cls)
        m = p.children[0]
        assert len(m.children) == 1
        assert isinstance(m.children[0], ast.Text)
        assert m.children[0].text == u'foo'
        assert m.start == ast.Location(1, 1)
        assert m.end == ast.Location(1, len(markup_string % u'foo') + 1)
        assert isinstance(p.children[1], ast.Text)
        t = p.children[1]
        assert t.text == u'bar'
        assert t.start == ast.Location(1, len(markup_string % u'foo') + 1)
        assert t.end == ast.Location(1, len(markup_string % u'foo') + len(u'bar') + 1)
        assert isinstance(p.children[2], node_cls)
        m = p.children[2]
        assert len(m.children) == 1
        assert isinstance(m.children[0], ast.Text)
        assert m.children[0].text == u'baz'
        assert m.start == ast.Location(1, len(markup_string % u'foo') + len(u'bar') + 1)
        assert m.end == ast.Location(1, len(code) + 1)


class TestEmphasis(InlineMarkupTest):
    @pytest.fixture
    def node_cls(self):
        return ast.Emphasis

    @pytest.fixture
    def markup_string(self):
        return u'*%s*'

    def test_escaping(self):
        document = Parser.from_string(u'\*foo\*').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'*foo*'

    def test_missing_closing_asterisk(self):
        document = Parser.from_string(u'*foo').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'*foo'

    def test_missing_opening_asterisk(self):
        document = Parser.from_string(u'foo*').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo*'


class TestStrong(InlineMarkupTest):
    @pytest.fixture
    def node_cls(self):
        return ast.Strong

    @pytest.fixture
    def markup_string(self):
        return u'**%s**'

    def test_escaping(self):
        document = Parser.from_string(u'\*\*foo\*\*').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'**foo**'

    def test_missing_closing_double_asterisk(self):
        document = Parser.from_string(u'**foo').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'**foo'

    def test_missing_opening_double_asterisk(self):
        document = Parser.from_string(u'foo**').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo**'


class TestReference(object):
    def test_only(self):
        document = Parser.from_string(u'[foo]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert p.start == ast.Location(1, 1)
        assert p.end == ast.Location(1, 6)
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None

    def test_only_missing_closing_bracket(self):
        document = Parser.from_string(u'[foo').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'[foo'

    def test_only_missing_target(self):
        document = Parser.from_string(u'[]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'[]'

    def test_only_missing_target_closing_bracket(self):
        document = Parser.from_string(u'[').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'['

    def test_only_with_type(self):
        document = Parser.from_string(u'[foo|bar]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert p.start == ast.Location(1, 1)
        assert p.end == ast.Location(1, 10)
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 10)
        assert r.type == u'foo'
        assert r.type.start == ast.Location(1, 2)
        assert r.type.end == ast.Location(1, 5)
        assert r.target == r.text == u'bar'
        assert r.target.start == r.text.start == ast.Location(1, 6)
        assert r.target.end == r.text.end == ast.Location(1, 9)

    def test_only_with_type_missing_closing_bracket(self):
        document = Parser.from_string(u'[foo|bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert p.children[0].text == u'[foo|bar'

    def test_only_with_type_missing_target(self):
        document = Parser.from_string(u'[foo|]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert p.children[0].text == u'[foo|]'

    def test_only_with_type_missing_target_closing_bracket(self):
        document = Parser.from_string(u'[foo|').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert p.children[0].text == u'[foo|'

    def test_only_with_inline_definition(self):
        document = Parser.from_string(u'[foo](bar)').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 11)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition == u'bar'
        assert r.definition.start == ast.Location(1, 7)
        assert r.definition.end == ast.Location(1, 10)

    def test_only_with_inline_definition_missing_closing_paren(self):
        document = Parser.from_string(u'[foo](bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'(bar'

    def test_only_with_inline_definition_missing_definition(self):
        document = Parser.from_string(u'[foo]()').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'()'

    def test_only_with_inline_definition_missing_definition_closing_paren(self):
        document = Parser.from_string(u'[foo](').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'('

    def test_only_with_type_and_inline_definition(self):
        document = Parser.from_string(u'[foo|bar](baz)').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 15)
        assert r.type == u'foo'
        assert r.type.start == ast.Location(1, 2)
        assert r.type.end == ast.Location(1, 5)
        assert r.target == r.text == u'bar'
        assert r.target.start == r.text.start == ast.Location(1, 6)
        assert r.target.end == r.text.end == ast.Location(1, 9)
        assert r.definition == u'baz'
        assert r.definition.start == ast.Location(1, 11)
        assert r.definition.end == ast.Location(1, 14)

    def test_only_with_type_and_inline_definition_missing_paren(self):
        document = Parser.from_string(u'[foo|bar](baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 10)
        assert r.type == u'foo'
        assert r.type.start == ast.Location(1, 2)
        assert r.type.end == ast.Location(1, 5)
        assert r.target == r.text == u'bar'
        assert r.target.start == r.text.start == ast.Location(1, 6)
        assert r.target.end == r.text.end == ast.Location(1, 9)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'(baz'

    def test_only_with_type_and_inline_definition_missing_definition(self):
        document = Parser.from_string(u'[foo|bar]()').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 10)
        assert r.type == u'foo'
        assert r.type.start == ast.Location(1, 2)
        assert r.type.end == ast.Location(1, 5)
        assert r.target == r.text == u'bar'
        assert r.target.start == r.text.start == ast.Location(1, 6)
        assert r.target.end == r.text.end == ast.Location(1, 9)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'()'

    def test_only_with_type_and_inline_definition_missing_definition_paren(self):
        document = Parser.from_string(u'[foo|bar](').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 10)
        assert r.type == u'foo'
        assert r.type.start == ast.Location(1, 2)
        assert r.type.end == ast.Location(1, 5)
        assert r.target == r.text == u'bar'
        assert r.target.start == r.text.start == ast.Location(1, 6)
        assert r.target.end == r.text.end == ast.Location(1, 9)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'('

    def test_only_with_text(self):
        document = Parser.from_string(u'[foo][bar]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 11)
        assert r.type is None
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.target == u'bar'
        assert r.target.start == ast.Location(1, 7)
        assert r.target.end == ast.Location(1, 10)
        assert r.definition is None

    def test_only_with_text_missing_bracket(self):
        document = Parser.from_string(u'[foo][bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'[bar'

    def test_only_with_text_missing_target(self):
        document = Parser.from_string(u'[foo][]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'[]'

    def test_only_with_text_missing_target_bracket(self):
        document = Parser.from_string(u'[foo][').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'['

    def test_only_with_text_and_type(self):
        document = Parser.from_string(u'[foo][bar|baz]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 15)
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.type == u'bar'
        assert r.type.start == ast.Location(1, 7)
        assert r.type.end == ast.Location(1, 10)
        assert r.target == u'baz'
        assert r.target.start == ast.Location(1, 11)
        assert r.target.end == ast.Location(1, 14)
        assert r.definition is None

    def test_only_with_text_and_type_missing_bracket(self):
        document = Parser.from_string(u'[foo][bar|baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'[bar|baz'

    def test_only_with_text_and_type_missing_target(self):
        document = Parser.from_string(u'[foo][bar|]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'[bar|]'

    def test_only_with_text_and_type_missing_target_bracket(self):
        document = Parser.from_string(u'[foo][bar|').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 6)
        assert r.type is None
        assert r.target == r.text == u'foo'
        assert r.target.start == r.text.start == ast.Location(1, 2)
        assert r.target.end == r.text.end == ast.Location(1, 5)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'[bar|'

    def test_only_with_text_and_definition(self):
        document = Parser.from_string(u'[foo][bar](baz)').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 16)
        assert r.type is None
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.target == u'bar'
        assert r.target.start == ast.Location(1, 7)
        assert r.target.end == ast.Location(1, 10)
        assert r.definition == u'baz'
        assert r.definition.start == ast.Location(1, 12)
        assert r.definition.end == ast.Location(1, 15)

    def test_only_with_text_and_definition_missing_paren(self):
        document = Parser.from_string(u'[foo][bar](baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 11)
        assert r.type is None
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.target == u'bar'
        assert r.target.start == ast.Location(1, 7)
        assert r.target.end == ast.Location(1, 10)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'(baz'

    def test_only_with_text_and_definition_missing_target(self):
        document = Parser.from_string(u'[foo][bar]()').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 11)
        assert r.type is None
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.target == u'bar'
        assert r.target.start == ast.Location(1, 7)
        assert r.target.end == ast.Location(1, 10)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'()'

    def test_only_with_text_and_definition_missing_target_paren(self):
        document = Parser.from_string(u'[foo][bar](').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 11)
        assert r.type is None
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.target == u'bar'
        assert r.target.start == ast.Location(1, 7)
        assert r.target.end == ast.Location(1, 10)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'('

    def test_only_with_text_and_type_and_definition(self):
        document = Parser.from_string(u'[foo][bar|baz](spam)').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 21)
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.type == u'bar'
        assert r.type.start == ast.Location(1, 7)
        assert r.type.end == ast.Location(1, 10)
        assert r.target == u'baz'
        assert r.target.start == ast.Location(1, 11)
        assert r.target.end == ast.Location(1, 14)
        assert r.definition == u'spam'
        assert r.definition.start == ast.Location(1, 16)
        assert r.definition.end == ast.Location(1, 20)

    def test_only_with_text_and_type_and_definition_missing_paren(self):
        document = Parser.from_string(u'[foo][bar|baz](spam').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 15)
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.type == u'bar'
        assert r.type.start == ast.Location(1, 7)
        assert r.type.end == ast.Location(1, 10)
        assert r.target == u'baz'
        assert r.target.start == ast.Location(1, 11)
        assert r.target.end == ast.Location(1, 14)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'(spam'

    def test_only_with_text_and_type_and_definition_missing_definition(self):
        document = Parser.from_string(u'[foo][bar|baz]()').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 15)
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.type == u'bar'
        assert r.type.start == ast.Location(1, 7)
        assert r.type.end == ast.Location(1, 10)
        assert r.target == u'baz'
        assert r.target.start == ast.Location(1, 11)
        assert r.target.end == ast.Location(1, 14)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'()'

    def test_only_with_text_and_type_and_definition_missing_definition_paren(self):
        document = Parser.from_string(u'[foo][bar|baz](').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 2
        assert isinstance(p.children[0], ast.Reference)
        r = p.children[0]
        assert r.start == ast.Location(1, 1)
        assert r.end == ast.Location(1, 15)
        assert r.text == u'foo'
        assert r.text.start == ast.Location(1, 2)
        assert r.text.end == ast.Location(1, 5)
        assert r.type == u'bar'
        assert r.type.start == ast.Location(1, 7)
        assert r.type.end == ast.Location(1, 10)
        assert r.target == u'baz'
        assert r.target.start == ast.Location(1, 11)
        assert r.target.end == ast.Location(1, 14)
        assert r.definition is None
        assert isinstance(p.children[1], ast.Text)
        assert p.children[1].text == u'('

    def test_escaping(self):
        document = Parser.from_string(u'\[foo\]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'[foo]'

        document = Parser.from_string(u'[foo\]bar]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        assert p.children[0].type is None
        assert p.children[0].target == p.children[0].text == u'foo]bar'

        document = Parser.from_string(u'[foo\|bar|baz]').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Reference)
        assert p.children[0].type == u'foo|bar'
        assert p.children[0].target == p.children[0].text == u'baz'


@pytest.mark.parametrize(('string', 'text', 'level'), [
    (u'# Hello', u'Hello', 1),
    (u'## Hello', u'Hello', 2)
])
def test_header(string, text, level):
    document = Parser.from_string(string).parse()
    assert len(document.children) == 1
    assert isinstance(document.children[0], ast.Header)
    h = document.children[0]
    assert h.text == text
    assert h.level == level
    assert h.start == ast.Location(1, 1)
    assert h.end == ast.Location(1, 1 + len(string))


class TestUnorderedList(object):
    def test_not_a_list(self):
        document = Parser.from_string(u'- this paragraph begins with an\n'
                                      u'asterisk, it\'s not a list\n'
                                      u'though.').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == (
            u'- this paragraph begins with '
            u'an asterisk, it\'s not a list '
            u'though.'
        )

    def test_simple(self):
        document = Parser.from_string(u'- foo\n'
                                      u'- bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.UnorderedList)
        list = document.children[0]
        assert len(list.children) == 2
        for i, text in enumerate([u'foo', u'bar']):
            assert isinstance(list.children[i], ast.ListItem)
            item = list.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            p = item.children[0]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text

    def test_multiple_line_items(self):
        document = Parser.from_string(u'- foo\n'
                                      u'  bar\n'
                                      u'- baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.UnorderedList)
        list = document.children[0]
        assert len(list.children) == 2
        for i, text in enumerate([u'foo bar', u'baz']):
            assert isinstance(list.children[i], ast.ListItem)
            item = list.children[i]
            assert len(item.children) == 1
            assert isinstance(item.children[0], ast.Paragraph)
            p = item.children[0]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text

    def test_bad_multiple_line_items(self):
        document = Parser.from_string(u'- foo\n'
                                      u' bar\n'
                                      u'- baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'- foo  bar - baz'

    def test_nested(self):
        document = Parser.from_string(u'- - foo\n'
                                      u'  - bar\n'
                                      u'  - - baz\n'
                                      u'- baz').parse()
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
            p = item.children[0]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text

        assert isinstance(nested.children[2], ast.ListItem)
        item = nested.children[2]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.UnorderedList)
        double_nested = item.children[0]
        assert len(double_nested.children) == 1
        item = double_nested.children[0]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        p = item.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'baz'

        assert isinstance(list.children[1], ast.ListItem)
        item = list.children[1]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        p = item.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'baz'

    def test_multiple_block_items(self):
        document = Parser.from_string(u'- foo\n'
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
            p = item.children[i]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text


class TestOrderedList(object):
    def test_not_a_list(self):
        document = Parser.from_string(u'1. this paragraph begins with a\n'
                                      u'number, it\'s not a list\n'
                                      u'though.').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == (
            u'1. this paragraph begins with '
            u'a number, it\'s not a list '
            u'though.'
        )

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
            p = item.children[0]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text

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
            p = item.children[0]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text

    def test_bad_multiple_line_items(self):
        document = Parser.from_string(u'1. foo\n'
                                      u'  bar\n'
                                      u'2. baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Paragraph)
        p = document.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'1. foo   bar 2. baz'

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
            p = item.children[0]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text

        assert isinstance(nested.children[2], ast.ListItem)
        item = nested.children[2]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.OrderedList)
        double_nested = item.children[0]
        assert len(double_nested.children) == 1
        item = double_nested.children[0]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        p = item.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'baz'

        assert isinstance(list.children[1], ast.ListItem)
        item = list.children[1]
        assert len(item.children) == 1
        assert isinstance(item.children[0], ast.Paragraph)
        p = item.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'baz'

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
            p = item.children[i]
            assert len(p.children) == 1
            assert isinstance(p.children[0], ast.Text)
            assert p.children[0].text == text


class TestDefinition(object):
    def test_simple(self):
        document = Parser.from_string(u'[foo]: bar').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Definition)
        d = document.children[0]
        assert d.type is None
        assert d.source == u'foo'
        assert d.signature == u'bar'
        assert d.body == []

    def test_simple_with_type(self):
        document = Parser.from_string(u'[foo|bar]: baz').parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.Definition)
        d = document.children[0]
        assert d.type == u'foo'
        assert d.source == u'bar'
        assert d.signature == u'baz'
        assert d.body == []

    def test_simple_with_body(self):
        document = Parser.from_string(
            u'[foo]: bar\n'
            u' hello\n'
            u' world\n'
            u'\n'
            u'blubb'
        ).parse()
        assert len(document.children) == 2
        assert isinstance(document.children[0], ast.Definition)
        d = document.children[0]
        assert d.type is None
        assert d.source == u'foo'
        assert d.signature == u'bar'
        assert d.body == [u'hello', u'world']

        assert isinstance(document.children[1], ast.Paragraph)
        p = document.children[1]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'blubb'


class TestQuote(object):
    def test_simple(self):
        document = Parser.from_string(
            u'> foo'
        ).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.BlockQuote)
        b = document.children[0]
        assert len(b.children) == 1
        assert isinstance(b.children[0], ast.Paragraph)
        p = b.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo'

    def test_multi_line(self):
        document = Parser.from_string(
            u'> foo\n'
            u'  bar'
        ).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.BlockQuote)
        b = document.children[0]
        assert len(b.children) == 1
        assert isinstance(b.children[0], ast.Paragraph)
        p = b.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo bar'

    def test_nesting(self):
        document = Parser.from_string(
            u'> > foo\n'
            u'\n'
            u'  bar'
        ).parse()
        assert len(document.children) == 1
        assert isinstance(document.children[0], ast.BlockQuote)
        outer_quote = document.children[0]
        assert len(outer_quote.children) == 2

        assert isinstance(outer_quote.children[0], ast.BlockQuote)
        inner_quote = outer_quote.children[0]
        assert len(inner_quote.children) == 1
        assert isinstance(inner_quote.children[0], ast.Paragraph)
        p = inner_quote.children[0]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'foo'

        assert isinstance(outer_quote.children[1], ast.Paragraph)
        p = outer_quote.children[1]
        assert len(p.children) == 1
        assert isinstance(p.children[0], ast.Text)
        assert p.children[0].text == u'bar'
