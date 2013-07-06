# coding: utf-8
"""
    tests.test_cli
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import subprocess

import pytest


class CLITest(object):
    def execute(self, command):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr


class TestMain(CLITest):
    @pytest.mark.parametrize('help_option', ['-h', '--help'])
    def test_help(self, help_option):
        returncode, stdout, stderr = self.execute(
            ['kurrent', help_option]
        )
        assert returncode == 0
        assert b'Usage:' in stdout
        assert b'Commands:' in stdout
        assert stderr == b''

    def test_version(self):
        returncode, stdout, stderr = self.execute(
            ['kurrent', '--version']
        )
        assert returncode == 0
        assert stdout == b'Kurrent 0.1.0-dev\n'
        assert stderr == b''

    @pytest.fixture
    def help_text(self):
        returncode, stdout, stderr = self.execute(
            ['kurrent', '--help']
        )
        assert returncode == 0
        assert stderr == b''
        return stdout

    def test_nonexisting_command(self, help_text):
        returncode, stdout, stderr = self.execute(
            ['kurrent', 'does-not-exist']
        )
        assert returncode == 1
        assert stderr == b"Error: 'does-not-exist' is not a kurrent command.\n\n"
        assert stdout == help_text


class TestBuild(CLITest):
    @pytest.fixture
    def help_text(self):
        returncode, stdout, stderr = self.execute(
            ['kurrent', 'build', '--help']
        )
        assert returncode == 0
        assert stderr == b''
        return stdout

    def test_nonexisting_builder(self, help_text):
        returncode, stdout, stderr = self.execute(
            ['kurrent', 'build', 'does-not-exist', 'kurrent', 'source']
        )
        assert returncode == 1
        assert stderr == b"Error: 'does-not-exist' is not a known builder.\n\n"
        assert stdout == help_text

    def test_nonexisting_writer(self, help_text):
        returncode, stdout, stderr = self.execute(
            ['kurrent', 'build', 'single', 'does-not-exist', 'source']
        )
        assert returncode == 1
        assert stderr == b"Error: 'does-not-exist' is not a known writer.\n\n"
        assert stdout == help_text
