# coding: utf-8
"""
    tests.test_transformations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent import ast
from kurrent.transformations import (
    TitleTransformation, DefaultDefinitionTransformation,
    DefaultReferenceTransformation
)


def test_title_transformation():
    document = ast.Document('<test>', children=[ast.Header(u'foo', 1)])
    TitleTransformation(document, {}).apply()
    assert document.title == u'foo'


def test_default_definition_transformation():
    definition = ast.Definition(None, u'foo', u'bar', [])
    document = ast.Document('<test>', children=[
        definition
    ])
    context = {}
    DefaultDefinitionTransformation(document, context).apply()
    assert context['definitions'][None][u'foo'] is definition


def test_default_reference_transformation():
    document = ast.Document('<test>', children=[
        ast.Reference(None, u'foo', u'foo')
    ])
    definition = ast.Definition(None, u'foo', u'bar', [])
    context = {
        'definitions': {
            None: {
                u'foo': definition
            }
        }
    }
    assert document.children[0].definition is None
    DefaultReferenceTransformation(document, context).apply()
    assert document.children[0].definition is definition


def test_default_definition_reference_transformation():
    definition = ast.Definition(None, u'foo', u'bar', [])
    document = ast.Document('<test>', children=[
        ast.Reference(None, u'foo', u'foo'),
        definition
    ])
    context = {}
    DefaultDefinitionTransformation(document, context).apply()
    assert document.children[0].definition is None
    DefaultReferenceTransformation(document, context).apply()
    assert document.children[0].definition is definition
