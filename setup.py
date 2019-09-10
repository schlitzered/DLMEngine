from setuptools import setup, find_packages

setup(
    name='DlmEngine',
    version='0.0.2',
    description='DlmEngine, distributed lock implementation on top of MongoDB and Redis',
    long_description="""
DLMEngine implements a restful interface that can be used to implement distributed locks.

The main intention was to orchestrate automated system updates, so only one server at a time will do a update.

Copyright (c) 2019, Stephan Schultchen.

License: MIT (see LICENSE for details)
    """,
    packages=find_packages(),
    scripts=[
        'contrib/dlm_engine',
    ],
    url='https://github.com/schlitzered/DlmEngine',
    license='MIT',
    author='schlitzer',
    author_email='stephan.schultchen@gmail.com',
    include_package_data=True,
    test_suite='test',
    platforms='posix',
    classifiers=[
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3'
    ],
    install_requires=[
        "aiohttp",
        "motor",
        "jsonschema",
        "pyyaml",
        "passlib",
        "aioredis",
    ],
    keywords=[
        'dlm', 'distributes lock manager'
    ]
)
