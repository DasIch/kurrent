# coding: utf-8
"""
    kurrent.parser
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import io
import re
import codecs
from itertools import groupby

from . import ast
from .utils import PushableIterator
from ._compat import implements_iterator, text_type, PY2, iteritems


# Python 3.3 does not support ur'' syntax
_header_re = re.compile(br'(#+)\s*(.*)'.decode('utf-8'))
_ordered_list_item_re = re.compile(br'(\d+\.)\s*(.*)'.decode('utf-8'))
_definition_re = re.compile(
    br"""
        \[
        ((?:
            [^\]]| # non-bracket
            \\\]   # escaped-bracket
        )*)
        \]:
        \s*
        (.*)
        \s*
    """.decode('utf-8'),
    re.VERBOSE
)
_definition_bracket_re = re.compile(
    br"""
        ((?:
            [^\]\|]|
            \\\]
        )*)
        (?:
            \|
            ((?:
                [^\]]|
                \\\]
            )*)
        )?
    """.decode('utf-8'),
    re.VERBOSE
)


def escaped(regex):
    return (u'\\\\' + regex, None)


class InlineTokenizer(object):
    states = {
        None: [
            (u'(\*\*)', u'**'),
            (u'(\*)', u'*'),
            escaped(u'(\*)'),
            escaped(u'(\[)'),
            (u'(\[)', u'[', 'push', 'reference'),
            escaped(u'(\])'),
            escaped(u'(\|)')
        ],
        'reference': [
            (u'(\]\()', u']('),
            (u'(\])', u']', 'pop'),
            escaped(u'(\])'),
            (u'(\|)', u'|'),
            escaped(u'(\|)'),
            (u'(\))', u')', 'pop'),
            escaped(u'(\))')
        ]
    }

    def __init__(self, lines):
        self.lines = lines

        self.states = self._compile_states(self.states)
        self.state_stack = [None]

    @property
    def state(self):
        return self.states[self.state_stack[-1]]

    def _compile_states(self, states):
        rv = {}
        for identifier, state in iteritems(states):
            rv[identifier] = compiled_state = []
            for rule in state:
                method = None
                args = []
                if len(rule) == 2:
                    regex, label = rule
                elif len(rule) == 3:
                    regex, label, method = rule
                elif len(rule) > 3:
                    regex, label, method = rule[:3]
                    args = rule[3:]
                else:
                    assert False, (identifier, rule)
                compiled_state.append((re.compile(regex), label, method, args))
        return rv

    def __iter__(self):
        first = True
        end = -1
        for line in self.lines:
            if first:
                first = False
            else:
                yield Line(u' ', line.lineno - 1, end), None
            for mark, group in groupby(self.tokenize(line), lambda part: part[1]):
                lexeme, mark = next(group)
                for continuing_lexeme, _ in group:
                    lexeme += continuing_lexeme
                yield lexeme, mark
                end = lexeme.columnno
        assert self.state_stack == [None]

    def tokenize(self, line):
        columnno = text_columnno = 0
        text = []
        while line[columnno:]:
            for regex, label, method, args in self.state:
                match = regex.match(line, columnno)
                if match is not None:
                    break
            else:
                if not text:
                    text_columnno = columnno
                text.append(line[columnno:columnno + 1])
                columnno += 1
            if match is not None:
                if text:
                    yield Line(u''.join(text), line.lineno, text_columnno + 1), None
                    text = []
                yield Line(match.group(1), line.lineno, columnno + 1), label
                if match.end() <= columnno:
                    assert False
                columnno = match.end()
                if method is not None:
                    getattr(self, method)(*args)
        if text:
            yield Line(u''.join(text), line.lineno, text_columnno + 1), None
            text = []

    def push(self, state):
        self.state_stack.append(state)

    def pop(self):
        self.state_stack.pop()


class Line(text_type):
    def __new__(cls, string, lineno, columnno):
        self = super(Line, cls).__new__(cls, string)
        self.lineno = lineno
        self.columnno = columnno
        return self

    @property
    def start(self):
        return ast.Location(self.lineno, self.columnno)

    @property
    def end(self):
        return ast.Location(self.lineno, self.columnno + len(self))

    def __add__(self, other):
        if isinstance(other, self.__class__):
            rv = super(Line, self).__add__(other)
            return Line(rv, self.lineno, self.columnno)
        return NotImplemented


@implements_iterator
class LineIterator(PushableIterator):
    def __init__(self, lines, lineno=0, columnno=1):
        super(LineIterator, self).__init__(lines)
        self.lineno = lineno
        self.columnno = columnno

    def __next__(self):
        try:
            if PY2:
                line = super(LineIterator, self).next()
            else:
                line = super(LineIterator, self).__next__()
        except UnicodeDecodeError:
            raise DocumentError(
                u'Could not decode characters in line %d, using %s.' % (
                    self.lineno, u'utf-8'
                )
            )
        self.lineno += 1
        return Line(line.rstrip(u'\r\n'), self.lineno, self.columnno)

    def push(self, line):
        self.lineno -= 1
        super(LineIterator, self).push(line)

    def until(self, condition):
        def inner():
            while True:
                line = next(self)
                if condition(line):
                    self.push(line)
                    break
                else:
                    yield line
        return self.__class__(inner(), self.lineno, self.columnno)

    def exhaust_until(self, condition):
        list(self.until(condition))

    def next_block(self):
        lines = []
        line = next(self)
        while True:
            lines.append(line)
            try:
                line = next(self)
                if not line:
                    self.exhaust_until(lambda line: line.strip())
                    line = next(self)
                    if line.startswith(u' '):
                        lines.append(u'')
                    else:
                        self.push(line)
                        break
            except StopIteration:
                break
        return self.__class__(lines, lines[0].lineno - 1, lines[0].columnno)

    def blockwise(self):
        while True:
            yield self.next_block()

    def unindented(self, spaces=None):
        if spaces is None:
            try:
                line = next(self)
            except StopIteration:
                return []
            self.push(line)
            spaces = len(line) - len(line.lstrip())
        def inner():
            for line in self:
                if line:
                    if len(line) < spaces or line[:spaces].strip():
                        raise BadPath()
                    line = line[spaces:]
                yield line
        return self.__class__(inner(), self.lineno, self.columnno + spaces)


class BadPath(BaseException):
    pass


class DocumentError(Exception):
    pass


class Parser(object):
    encoding = 'utf-8'

    @classmethod
    def from_path(cls, path):
        return cls(codecs.open(path, 'r', encodings=cls.encoding),
                   filename=path)

    @classmethod
    def from_string(cls, string):
        return cls(io.StringIO(string), filename='<string>')

    @classmethod
    def from_bytes(cls, bytes):
        bytestream = io.BytesIO(bytes)
        stringstream = codecs.lookup(cls.encoding).streamreader(bytestream)
        return cls(stringstream, filename='<string>')

    def __init__(self, stream, filename=None):
        self.stream = stream
        if filename is None:
            self.filename = self.stream.name
        else:
            self.filename = filename

        self.lines = LineIterator(self.stream)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if hasattr(self.stream, 'close'):
            self.stream.close()

    def parse(self):
        return ast.Document(
            self.filename,
            children=[
                self.parse_block(list(block)) for block in self.lines.blockwise()
            ]
        )

    def parse_block(self, lines):
        if len(lines) == 1:
            line = lines[0]
            if line.startswith(u'#'):
                return self.parse_header(line)
        if lines[0].startswith(u'-'):
            try:
                return self.parse_unordered_list(lines)
            except BadPath:
                pass
        if _ordered_list_item_re.match(lines[0]):
            try:
                return self.parse_ordered_list(lines)
            except BadPath:
                pass
        if _definition_re.match(lines[0]):
            return self.parse_definition(lines)
        return self.parse_paragraph(lines)

    def parse_paragraph(self, lines):
        return ast.Paragraph(children=self.parse_inline(lines))

    def parse_inline(self, lines):
        inline_tokens = PushableIterator(InlineTokenizer(lines))
        return self._parse_inline(inline_tokens)

    def _parse_inline(self, inline_tokens):
        rv = []
        for lexeme, mark in inline_tokens:
            if mark is None:
                if rv and isinstance(rv[-1], ast.Text):
                    rv[-1].text += lexeme
                    rv[-1].end = lexeme.end
                else:
                    rv.append(ast.Text(lexeme, lexeme.start, lexeme.end))
            elif mark == u'**':
                rv.append(self.parse_strong(inline_tokens, lexeme.start))
            elif mark == u'*':
                rv.append(self.parse_emphasis(inline_tokens, lexeme.start))
            elif mark == u'[':
                rv.append(self.parse_reference(inline_tokens, lexeme.start))
            else:
                raise NotImplementedError(lexeme, mark)
        return rv

    def parse_strong(self, tokens, start):
        rv = ast.Strong()
        rv.start = start
        for lexeme, mark in tokens:
            if mark == u'**':
                rv.end = lexeme.end
                break
            elif mark is None:
                if rv.children and isinstance(rv.children[-1], ast.Text):
                    rv.children[-1].text += lexeme
                    rv.children[-1].end = lexeme.end
                else:
                    rv.add_child(ast.Text(lexeme, lexeme.start, lexeme.end))
            else:
                raise NotImplementedError(lexeme, mark)
        return rv

    def parse_emphasis(self, tokens, start):
        rv = ast.Emphasis()
        rv.start = start
        for lexeme, mark in tokens:
            if mark == u'*':
                rv.end = lexeme.end
                break
            elif mark is None:
                if rv.children and isinstance(rv.children[-1], ast.Text):
                    rv.children[-1].text += lexeme
                    rv.children[-1].end = lexeme.end
                else:
                    rv.add_child(ast.Text(lexeme, lexeme.start, lexeme.end))
            else:
                raise NotImplementedError(lexeme, mark)
        return rv

    def parse_reference(self, tokens, start):
        type = definition = None
        target, mark = next(tokens)
        assert mark is None
        lexeme, mark = next(tokens)
        if mark == u']':
            end = lexeme.end
        elif mark == u'|':
            type = target
            target, mark = next(tokens)
            assert mark is None
            end_lexeme, mark = next(tokens)
            end = end_lexeme.end
            assert mark in [u']', u'](']
            if mark == u'](':
                definition, mark = next(tokens)
                end_lexeme, mark = next(tokens)
                end = end_lexeme.end
                assert mark == u')'
        elif mark == u'](':
            definition, mark = next(tokens)
            end_lexeme, mark = next(tokens)
            end = end_lexeme.end
            assert mark == u')'
        return ast.Reference(type, target, definition, start=start,
                             end=end)

    def parse_header(self, line):
        match = _header_re.match(line)
        level_indicator = match.group(1)
        text = match.group(2)
        return ast.Header(text, len(level_indicator), line.start, line.end)

    def parse_unordered_list(self, lines):
        return self._parse_list(
            ast.UnorderedList,
            lambda l: l.startswith(u'-'),
            lambda l: l[1:].lstrip(),
            lines
        )

    def parse_ordered_list(self, lines):
        def strip(line):
            return _ordered_list_item_re.match(line).group(2)
        return self._parse_list(
            ast.OrderedList,
            _ordered_list_item_re.match,
            strip,
            lines
        )

    def _parse_list(self, node_cls, match, strip, lines):
        rv = node_cls()
        lineiter = LineIterator(lines)
        for line in lineiter:
            if not match(line):
                raise BadPath()
            stripped = strip(line)
            indentation_level = len(line) - len(stripped)
            lineiter.push(u' ' * indentation_level + stripped)
            rv.add_child(
                ast.ListItem([
                    self.parse_block(list(block))
                    for block in
                    lineiter.until(match).unindented(indentation_level).blockwise()
                ])
            )
        return rv

    def parse_definition(self, lines):
        match = _definition_re.match(lines[0])
        bracket = match.group(1)
        signature = match.group(2)
        match = _definition_bracket_re.match(bracket)
        if match.group(2) is None:
            type = None
            source = match.group(1)
        else:
            type, source = match.groups()
        body = list(LineIterator(lines[1:]).unindented())
        return ast.Definition(type, source, signature, body)
