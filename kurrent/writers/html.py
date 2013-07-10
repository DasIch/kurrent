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


class HTML5Writer(Writer):
    def write_Text(self, node):
        self.write(escape(node.text))

    @contextmanager
    def write_Paragraph(self, node):
        self.write(u'<p>')
        yield True
        self.write(u'</p>')

    def write_Header(self, node):
        self.write(u'<h%d>' % node.level)
        self.write(escape(node.text))
        self.write(u'</h%d>' % node.level)

    @contextmanager
    def write_UnorderedList(self, node):
        self.write(u'<ul>')
        yield True
        self.write(u'</ul>')

    @contextmanager
    def write_ListItem(self, node):
        self.write(u'<li>')
        yield True
        self.write(u'</li>')

    @contextmanager
    def write_Document(self, node):
        self.write(u'<!doctype html>')
        self.write(u'<title>%s</title>' % (
            escape(node.metadata.get('title', u''))
        ))
        yield True

    @contextmanager
    def write_Emphasis(self, node):
        self.write(u'<em>')
        yield True
        self.write(u'</em>')

    @contextmanager
    def write_Strong(self, node):
        self.write(u'<strong>')
        yield True
        self.write(u'</strong>')

    def write_Reference(self, node):
        self.write(u'<a href="')
        self.write(node.definition)
        self.write(u'">')
        self.write(escape(node.text))
        self.write(u'</a>')

    def write_Definition(self, node):
        # prevents NotImplementedError, we ignore Definitions
        pass

    @contextmanager
    def write_BlockQuote(self, node):
        self.write(u'<blockquote>')
        yield True
        self.write(u'</blockquote>')
