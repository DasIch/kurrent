# coding: utf-8
"""
    kurrent.builders
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import codecs

from kurrent.parser import Parser
from kurrent.transformations import CORE_TRANSFORMATIONS


class SingleDocumentBuilder(object):
    def __init__(self, source_path, target_path, writer_cls):
        self.source_path = source_path
        self.target_path = target_path
        self.writer_cls = writer_cls

    def build(self):
        document = self.parse()
        self.apply_transformations(document)
        self.write(document)

    def parse(self):
        with Parser.from_path(self.source_path) as parser:
            return parser.parse()

    def apply_transformations(self, document):
        context = {}
        for transformation_cls in CORE_TRANSFORMATIONS:
            transformation_cls(document, context).apply()

    def write(self, document):
        with codecs.open(self.target_path, 'w', encoding='utf-8') as file:
            self.writer_cls(file).write_node(document)
