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
        self.document.metadata['title'] = node.text
        raise StopTransformation()


class LinkExtensionTransformation(Transformation):
    def select_node(self, node):
        return isinstance(node, ast.Extension) and node.type is None

    def transform(self, node):
        links = self.context.setdefault('links', {})
        assert node.primary not in links, links
        assert not node.body, node.body
        links[node.primary] = node.secondary
        node.remove_from_parent()


class LinkInlineExtensionTransformation(Transformation):
    def select_node(self, node):
        return isinstance(node, ast.InlineExtension) and node.type is None

    def transform(self, node):
        links = self.context.get('links', {})
        if node.primary in links:
            target = links[node.primary]
            text = node.primary if node.text is None else node.text
        elif node.text is None:
            target = text = node.primary
        else:
            target, text = node.primary, node.text
        assert node.secondary is None, node.secondary
        node.replace_in_parent(ast.Link(
            target, text, start=node.start, end=node.end
        ))


CORE_TRANSFORMATIONS = [TitleTransformation]
LINK_TRANSFORMATIONS = [
    LinkExtensionTransformation, LinkInlineExtensionTransformation
]
