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

from . import ast
from ._compat import implements_iterator, text_type


# Python 3.3 does not support ur'' syntax
_header_re = re.compile(br'(#+)\s*(.*)'.decode('utf-8'))
_ordered_list_item_re = re.compile(br'(\d+\.)\s*(.*)'.decode('utf-8'))


class Line(text_type):
    def __new__(cls, string, lineno, columnno):
        self = super(Line, cls).__new__(cls, string)
        self.lineno = lineno
        self.columnno = columnno
        return self


@implements_iterator
class LineIterator(object):
    def __init__(self, lines, lineno=0, columnno=1):
        self.lines = iter(lines)
        self.lineno = lineno
        self.columnno = columnno
        self.remaining = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining:
            line = self.remaining.pop()
        else:
            line = next(self.lines)
        self.lineno += 1
        return Line(line.rstrip(u'\r\n'), self.lineno, self.columnno)

    def push(self, line):
        self.lineno -= 1
        self.remaining.append(line)

    def push_many(self, lines):
        for line in lines:
            self.push(line)

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

    def next_block(self):
        lines = []
        line = next(self)
        while True:
            lines.append(line)
            try:
                line = next(self)
                if not line:
                    empty_lines = list(self.until(lambda line: line.strip()))
                    line = next(self)
                    if line.startswith(u' '):
                        lines.append(u'')
                    else:
                        self.push_many(empty_lines)
                        self.push(line)
                        break
            except StopIteration:
                break
        return self.__class__(lines, lines[0].lineno, lines[0].columnno)

    def blockwise(self):
        while True:
            yield self.next_block()

    def unindented(self, spaces):
        def inner():
            for line in self:
                if line:
                    if len(line) < spaces:
                        raise BadPath()
                    if line[:spaces].strip():
                        raise BadPath()
                    line = line[spaces:]
                yield line
        return self.__class__(inner(), self.lineno, self.columnno + spaces)


class ParserFlow(BaseException):
    pass


class BadPath(ParserFlow):
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
            [self.parse_block(list(block)) for block in self.lines.blockwise()]
        )

    def parse_block(self, lines):
        if len(lines) == 1:
            line = lines[0]
            if line.startswith(u'#'):
                return self.parse_header(line)
        if lines[0].startswith(u'*'):
            try:
                return self.parse_unordered_list(lines)
            except BadPath:
                pass
        if _ordered_list_item_re.match(lines[0]):
            try:
                return self.parse_ordered_list(lines)
            except BadPath:
                pass
        return self.parse_paragraph(lines)

    def parse_paragraph(self, lines):
        return ast.Paragraph(u' '.join(lines))

    def parse_header(self, line):
        match = _header_re.match(line)
        level_indicator = match.group(1)
        text = match.group(2)
        return ast.Header(text, len(level_indicator))

    def parse_unordered_list(self, lines):
        return self._parse_list(
            ast.UnorderedList,
            lambda l: l.startswith(u'*'),
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
            rv.children.append(
                ast.ListItem([
                    self.parse_block(list(block))
                    for block in
                    lineiter.until(match).unindented(indentation_level).blockwise()
                ])
            )
        return rv
