# coding: utf-8
import os
import codecs

from setuptools import setup


PACKAGE_PATH = os.path.join(os.path.dirname(__file__), 'kurrent')


def get_version():
    init_file_path = os.path.join(PACKAGE_PATH, '__init__.py')
    with codecs.open(init_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith(u'__version__'):
                return line.split(u'=')[1].replace(u"'", u'').strip()
    raise ValueError('__version__ not found in %s' % init_file_path)


setup(
    name='Kurrent',
    version=get_version(),
    license='BSD',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    url='https://github.com/DasIch/kurrent',
    packages=['kurrent', 'kurrent.writers'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'kurrent = kurrent.cli:main'
        ]
    },
    install_requires=[
        'MarkupSafe>=0.18',
        'docopt>=0.6.1'
    ],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Text Processing :: Markup'
    ]
)
