# -*- coding: utf-8 -*-
import codecs

from setuptools import setup


def get_version():
    with open('flake8_future_import.py') as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])


def get_long_description():
    with codecs.open('README.rst', 'r', 'utf-8') as f:
        return f.read()


setup(
    name='flake8-future-import',
    version=get_version(),
    description='__future__ import checker, plugin for flake8',
    long_description=get_long_description(),
    keywords='flake8 import future',
    maintainer='Fabian Neundorf',
    maintainer_email='CommodoreFabianus@gmx.de',
    url='https://github.com/xZise/flake8-import',
    license='MIT License',
    py_modules=['flake8_import'],
    zip_safe=False,
    entry_points={
        'flake8.extension': [
            'flake8-future-import = flake8_future_import:FutureImportChecker',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
    ],
)
