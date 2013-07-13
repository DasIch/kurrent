# coding: utf-8
"""
    tests.conftest
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_file_path(request):
    file_path = tempfile.mkstemp()[1]
    request.addfinalizer(lambda: os.remove(file_path))
    return file_path


@pytest.fixture
def temp_file_directory(request):
    directory_path = tempfile.mkdtemp()
    request.addfinalizer(lambda: shutil.rmtree(directory_path))
    return directory_path
