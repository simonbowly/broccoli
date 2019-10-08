#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os

from setuptools import find_packages, setup

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
here = os.path.abspath(os.path.dirname(__file__))
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

setup(
    name="broccoli",
    version="0.1.0",
    description="Rather Ordinary Computing Cluster",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Simon Bowly",
    author_email="simon.bowly@gmail.com",
    python_requires=">=3.7.0",
    url="simonbowly/broccoli",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    entry_points={"console_scripts": [
        "broccoli-node=broccoli.node:cli",
        "broccoli-update=broccoli.update:update",
        ]},
    install_requires=["click", "pyzmq", "msgpack"],
    include_package_data=True,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
