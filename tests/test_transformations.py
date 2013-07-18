# coding: utf-8
"""
    tests.test_transformations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent import ast
from kurrent.transformations import (
    TitleTransformation, LinkExtensionTransformation,
    LinkInlineExtensionTransformation
)


def test_title_transformation():
    document = ast.Document('<test>', children=[ast.Header(u'foo', 1)])
    TitleTransformation(document, {}).apply()
    assert document.metadata['title'] == u'foo'


def test_link_extension_transformation():
    document = ast.Document('<test>', children=[
        ast.Extension(None, u'text', secondary=u'target')
    ])
    context = {}
    LinkExtensionTransformation(document, context).apply()
    assert context['links'] == {u'text': u'target'}
    assert not document.children


class TestLinkInlineExtensionTransformation(object):
    def test_simple(self):
        document = ast.Document('<test>', children=[
            ast.InlineExtension(None, u'http://google.com')
        ])
        LinkInlineExtensionTransformation(document, {}).apply()
        assert isinstance(document.children[0], ast.Link)
        assert document.children[0].target == u'http://google.com'
        assert document.children[0].text == u'http://google.com'

    def test_with_text(self):
        document = ast.Document('<test>', children=[
            ast.InlineExtension(None, u'http://google.com', text=u'google')
        ])
        LinkInlineExtensionTransformation(document, {}).apply()
        assert isinstance(document.children[0], ast.Link)
        assert document.children[0].target == u'http://google.com'
        assert document.children[0].text == u'google'

    def test_from_context(self):
        document = ast.Document('<test>', children=[
            ast.InlineExtension(None, u'google')
        ])
        context = {'links': {u'google': u'http://google.com'}}
        LinkInlineExtensionTransformation(document, context).apply()
        assert isinstance(document.children[0], ast.Link)
        assert document.children[0].target == u'http://google.com'
        assert document.children[0].text == u'google'

    def test_from_context_with_text(self):
        document = ast.Document('<test>', children=[
            ast.InlineExtension(None, u'google', text=u'Google')
        ])
        context = {'links': {u'google': u'http://google.com'}}
        LinkInlineExtensionTransformation(document, context).apply()
        assert isinstance(document.children[0], ast.Link)
        assert document.children[0].target == u'http://google.com'
        assert document.children[0].text == u'Google'
