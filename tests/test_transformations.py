# coding: utf-8
"""
    tests.test_transformations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent import ast
from kurrent.transformations import TitleTransformation


def test_title_transformation():
    document = ast.Document('<test>', children=[ast.Header(u'foo', 1)])
    TitleTransformation(document).apply()
    assert document.title == u'foo'
