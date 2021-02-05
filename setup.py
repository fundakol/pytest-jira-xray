from setuptools import setup, find_packages

__version__ = '0.1.0'

with open('README.md', 'r') as fh:
    long_description = fh.read()

classifiers = [
    'Development Status :: 3 - Alpha',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
]

setup(
    name='pytest-jira-xray',
    version=__version__,
    packages=find_packages('src'),
    package_dir={"": "src"},
    url='https://github.com/fundakol/pytest-jira-xray',
    author='Lukasz Fundakowski',
    author_email='fundakol@yahoo.com',
    description='pytest plugin to integrate tests with JIRA XRAY',
    long_description=long_description,
    python_requires='>=3.6',
    install_requires=[
        'pytest',
        'requests'
    ],
    keywords='pytest JIRA XRAY',
    classifiers=classifiers,
    entry_points={
        'pytest11': [
            'xray = pytest_xray.plugin',
        ]
    },
)
