# coding: utf-8
"""
    kurrent.writers.html
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from contextlib import contextmanager

from markupsafe import escape

from .base import Writer


def make_block_writer(tag, indent=True, follow_with_newline=False):
    if indent:
        @contextmanager
        def write(self, node):
            self.write_line(u'<%s>' % tag)
            with self.indent(u'  '):
                yield True
            if follow_with_newline:
                self.newline()
            self.write_line(u'</%s>' % tag)
    else:
        @contextmanager
        def write(self, node):
            self.write(u'<%s>' % tag)
            yield True
            self.write(u'</%s>' % tag)
    return write


class HTML5Writer(Writer):
    @classmethod
    def get_file_extension(self, document):
        return '.html'

    def write_Text(self, node):
        self.write(escape(node.text))

    write_Paragraph = make_block_writer(u'p', follow_with_newline=True)
    write_ListItem = make_block_writer(u'li')
    write_OrderedList = make_block_writer(u'ol')
    write_UnorderedList = make_block_writer(u'ul')
    write_BlockQuote = make_block_writer(u'blockquote')
    write_Emphasis = make_block_writer(u'em', indent=False)
    write_Strong = make_block_writer(u'strong', indent=False)

    def write_Header(self, node):
        self.write(u'<h%d>' % node.level)
        self.write(escape(node.text))
        self.write(u'</h%d>' % node.level)
        self.newline()

    @contextmanager
    def write_Document(self, node):
        self.write_line(u'<!doctype html>')
        self.write_line(u'<title>%s</title>' % (
            escape(node.metadata.get('title', u''))
        ))
        yield True

    def write_Reference(self, node):
        self.write(u'<a href="')
        self.write(node.definition)
        self.write(u'">')
        self.write(escape(node.text))
        self.write(u'</a>')
        self.newline()

    def write_Definition(self, node):
        # prevents NotImplementedError, we ignore Definitions
        pass
