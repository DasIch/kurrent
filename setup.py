# coding: utf-8
from setuptools import setup


setup(
    name='Kurrent',
    version='0.1.0-dev',
    license='BSD',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    url='https://github.com/DasIch/kurrent',
    packages=['kurrent'],
    include_package_data=True,
    install_requires=['markupsafe>=0.18'],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Text Processing :: Markup'
    ]
)
