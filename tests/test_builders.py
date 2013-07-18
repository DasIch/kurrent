# coding: utf-8
"""
    tests.test_builders
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import re
import codecs
import textwrap

import pytest

from kurrent.builders import SingleDocumentBuilder
from kurrent.writers import KurrentWriter, HTML5Writer, ManWriter


TEST_DOCUMENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))


def read_file(path, encoding='utf-8'):
    with codecs.open(path, encoding=encoding) as file:
        return file.read()


class TestSingleDocumentBuilder(object):
    @pytest.mark.parametrize(('writer_cls', 'extension', 'expected_content'), [
        (KurrentWriter, '.kr', textwrap.dedent(u"""\
            # Test

            This is a test.""")),
        (HTML5Writer, '.html',
         u'<!doctype html>\n'
         u'<title>Test</title>\n'
         u'<h1>Test</h1>\n'
         u'<p>\n'
         u'  This is a test.\n'
         u'</p>'
        ),
        (ManWriter, u'.1',
         u'.TH "Test" "1" "[^"]+" ""\n'
         u'.SH "Test"\n'
         u'.P\n'
         u'This is a test.'
        )
    ])
    def test_simple(self, temp_file_directory, writer_cls, extension,
                    expected_content):
        SingleDocumentBuilder(
            os.path.join(TEST_DOCUMENT_DIRECTORY, 'single_document_test.kr'),
            temp_file_directory,
            writer_cls
        ).build()

        content = read_file(os.path.join(
            temp_file_directory,
            'single_document_test' + extension
        ))
        match = re.match(expected_content, content)
        assert match is not None, content
        assert match.group() == content

    def test_applies_writer_specific_transformations(self, temp_file_directory):
        # Links are specific to the HTML5 builder at the moment
        SingleDocumentBuilder(
            os.path.join(TEST_DOCUMENT_DIRECTORY, 'single_document_link_test.kr'),
            temp_file_directory,
            HTML5Writer
        ).build()

        content = read_file(os.path.join(
            temp_file_directory, 'single_document_link_test.html'
        ))
        assert content == (
            u'<!doctype html>\n'
            u'<title></title>\n'
            u'<p>\n  '
            u'<a href="http://google.com">http://google.com</a> '
            u'<a href="http://google.com">Google</a> '
            u'<a href="http://google.com">google</a>\n'
            u'</p>'
        )
