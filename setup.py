# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'ipdb',
    'tox',
]

setup(
    name='tornado-alf',
    version='0.4.0',
    description="OAuth Client For Tornado",
    long_description=open('README.rst').read(),
    keywords='oauth client client_credentials tornado',
    author=u'Globo.com',
    author_email='entretenimento1@corp.globo.com',
    url='https://github.com/globocom/tornado-alf',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    packages=find_packages(
        exclude=(
            'tests',
        ),
    ),
    include_package_data=True,
    install_requires=[
        'tornado>=3.0',
    ],
    extras_require={
        'tests': tests_require,
    },
)
