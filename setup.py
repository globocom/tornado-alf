# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='tornado-alf',
    version='0.2',
    description="OAuth Client For Tornado",
    long_description=open('README.rst').read(),
    keywords='oauth client client_credentials tornado',
    author=u'Globo.com',
    author_email='entretenimento1@corp.globo.com',
    url='https://github.com/globocom/tornado-alf',
    license='Proprietary',
    classifiers=['Intended Audience :: Developers'],
    packages=find_packages(
        exclude=(
            'tests',
        ),
    ),
    include_package_data=True,
    install_requires=[
        'tornado>=3.0',
    ],
)
