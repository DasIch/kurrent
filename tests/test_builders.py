# coding: utf-8
"""
    tests.test_builders
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import codecs
import textwrap

import pytest

from kurrent.builders import SingleDocumentBuilder
from kurrent.writers import KurrentWriter, HTML5Writer


TEST_DOCUMENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))


def read_file(path, encoding='utf-8'):
    with codecs.open(path, encoding=encoding) as file:
        return file.read()


@pytest.mark.parametrize(('writer_cls', 'expected_content'), [
    (KurrentWriter, textwrap.dedent(u"""\
        # Test

        This is a test.

    """)),
    (HTML5Writer,
     u'<!doctype html><title>Test</title><h1>Test</h1><p>This is a test.</p>'
    )
])
def test_single_document_builder_test(temp_file_path, writer_cls, expected_content):
    SingleDocumentBuilder(
        os.path.join(TEST_DOCUMENT_DIRECTORY, 'single_document_test.kr'),
        temp_file_path,
        writer_cls
    ).build()

    content = read_file(temp_file_path)
    assert content == expected_content
