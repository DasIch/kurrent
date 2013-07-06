# coding: utf-8
"""
    tests.test_cli
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import subprocess

import pytest


class TestMain(object):
    @pytest.mark.parametrize('help_option', ['-h', '--help'])
    def test_help(self, help_option):
        process = subprocess.Popen(
            ['kurrent', help_option],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 0
        assert b'Usage:' in stdout
        assert b'Commands:' in stdout
        assert stderr == b''

    def test_version(self):
        process = subprocess.Popen(
            ['kurrent', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 0
        assert stdout == b'Kurrent 0.1.0-dev\n'
        assert stderr == b''

    @pytest.fixture
    def help_text(self):
        process = subprocess.Popen(
            ['kurrent', '--help'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 0
        assert stderr == b''
        return stdout

    def test_nonexisting_command(self, help_text):
        process = subprocess.Popen(
            ['kurrent', 'does-not-exist'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 1
        assert stderr == b"Error: 'does-not-exist' is not a kurrent command.\n\n"

        assert stdout == help_text


class TestBuild(object):
    @pytest.fixture
    def help_text(self):
        process = subprocess.Popen(
            ['kurrent', 'build', '--help'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 0
        assert stderr == b''
        return stdout

    def test_nonexisting_builder(self, help_text):
        process = subprocess.Popen(
            ['kurrent', 'build', 'does-not-exist', 'kurrent', 'source'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 1
        assert stderr == b"Error: 'does-not-exist' is not a known builder.\n\n"
        assert stdout == help_text

    def test_nonexisting_writer(self, help_text):
        process = subprocess.Popen(
            ['kurrent', 'build', 'single', 'does-not-exist', 'source'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        assert process.returncode == 1
        assert stderr == b"Error: 'does-not-exist' is not a known writer.\n\n"
        assert stdout == help_text
