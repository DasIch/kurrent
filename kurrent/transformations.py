# coding: utf-8
"""
    kurrent.transformations
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from . import ast
from ._compat import ifilter


class StopTransformation(BaseException):
    pass


class Transformation(object):
    def __init__(self, document, context):
        self.document = document
        self.context = context

    def apply(self):
        for node in ifilter(self.select_node, self.document.traverse()):
            try:
                self.transform(node)
            except StopTransformation:
                break

    def select_node(self, node):
        raise NotImplementedError()

    def transform(self, node):
        raise NotImplementedError()


class TitleTransformation(Transformation):
    def select_node(self, node):
        return isinstance(node, ast.Header)

    def transform(self, node):
        self.document.title = node.text
        raise StopTransformation()


class DefaultDefinitionTransformation(Transformation):
    def select_node(self, node):
        return isinstance(node, ast.Definition) and node.type is None

    def transform(self, node):
        known_definitions = self.context.setdefault('definitions', {})
        known_default_definitions = known_definitions.setdefault(None, {})
        known_default_definitions[node.source] = node


class DefaultReferenceTransformation(Transformation):
    def select_node(self, node):
        return isinstance(node, ast.Reference) and node.type is None

    def transform(self, node):
        definitions = self.context.get('definitions', {}).get(None, {})
        node.definition = definitions[node.target]
