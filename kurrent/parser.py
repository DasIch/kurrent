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
from .utils import PushableIterator


_header_re = re.compile(ur'(#+)\s*(.*)')
_ordered_list_item_re = re.compile(ur'(\d+\.)\s*(.*)')


class LineIterator(PushableIterator):
    def next(self):
        return super(LineIterator, self).next().rstrip(u'\r\n')

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
        return lines

    def blockwise(self):
        while True:
            yield self.next_block()


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
        root = ast.Document(self.filename)
        for block in self.lines.blockwise():
            root.children.append(self.parse_block(block))
        return root

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
        lineiter = PushableIterator(lines)
        for line in lineiter:
            if not match(line):
                raise BadPath()
            itemlines = [strip(line)]
            indentation_level = len(line) - len(itemlines[0])
            for line in lineiter.until(match):
                if line:
                    if len(line) < indentation_level:
                        raise BadPath()
                    if line[:indentation_level].strip():
                        raise BadPath()
                    itemlines.append(line[indentation_level:])
                else:
                    itemlines.append(line)
            item = ast.ListItem()
            for block in LineIterator(itemlines).blockwise():
                item.children.append(self.parse_block(block))
            rv.children.append(item)
        return rv
