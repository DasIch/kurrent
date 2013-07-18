# coding: utf-8
"""
    kurrent.builders
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import codecs

from kurrent.parser import Parser
from kurrent.transformations import CORE_TRANSFORMATIONS


class SingleDocumentBuilder(object):
    def __init__(self, source_path, target_dir, writer_cls):
        self.source_path = source_path
        self.target_dir = target_dir
        self.writer_cls = writer_cls

    @property
    def transformations(self):
        return CORE_TRANSFORMATIONS + self.writer_cls.transformations

    def get_target_path(self, document):
        extension = self.writer_cls.get_file_extension(document)
        return os.path.join(
            self.target_dir,
            os.path.splitext(os.path.basename(self.source_path))[0] + extension)

    def build(self):
        document = self.parse()
        self.apply_transformations(document)
        self.write(document)

    def parse(self):
        with Parser.from_path(self.source_path) as parser:
            return parser.parse()

    def apply_transformations(self, document):
        context = {}
        for transformation_cls in self.transformations:
            transformation_cls(document, context).apply()

    def write(self, document):
        with codecs.open(self.get_target_path(document), 'w', encoding='utf-8') as file:
            self.writer_cls(file).write_node(document)
