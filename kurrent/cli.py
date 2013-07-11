# coding: utf-8
"""
    kurrent.cli
    ~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import print_function
import os
import sys
import textwrap

from docopt import docopt

from kurrent import __version__
from kurrent.builders import SingleDocumentBuilder
from kurrent.writers import HTML5Writer, KurrentWriter, ManWriter


BUILDERS = {
    'single': SingleDocumentBuilder
}
WRITERS = {
    'kurrent': KurrentWriter,
    'html5': HTML5Writer,
    'man': ManWriter
}


def main(argv=sys.argv):
    """
    Usage:
      kurrent [-h | --help] [--version] <command> [<args> ...]

    Commands:
      build
    """
    arguments = docopt(
        textwrap.dedent(main.__doc__),
        argv=argv[1:],
        version=u'Kurrent %s' % __version__,
        options_first=True
    )
    arguments['<args>'].insert(0, arguments['<command>'])
    if arguments['<command>'] == 'build':
        build(arguments['<args>'])
    else:
        print(
            u'Error: %r is not a kurrent command.\n' % arguments['<command>'],
            file=sys.stderr
        )
        try:
            main(['kurrent', '--help'])
        except SystemExit:
            sys.exit(1)

def build(argv):
    """
    Usage:
      kurrent build [-h | --help] <builder> <writer> <sources>...

    Builders:
      single  Builds a single document.

    Writers:
      kurrent  Creates a kurrent file.
      html5    Creates an HTML5 file.
      man      Creates a man page.
    """
    arguments = docopt(
        textwrap.dedent(build.__doc__),
        argv=argv
    )
    try:
        builder = BUILDERS[arguments['<builder>']]
    except KeyError:
        print(
            u'Error: %r is not a known builder.\n' % arguments['<builder>'],
            file=sys.stderr
        )
        try:
            build(['build', '--help'])
        except SystemExit:
            sys.exit(1)
    try:
        writer = WRITERS[arguments['<writer>']]
    except KeyError:
        print(
            u'Error: %r is not a known writer.\n' % arguments['<writer>'],
            file=sys.stderr
        )
        try:
            build(['build', '--help'])
        except SystemExit:
            sys.exit(1)
    for source in arguments['<sources>']:
        builder(source, os.path.dirname(source), writer).build()
