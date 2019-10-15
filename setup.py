#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import subprocess

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent

# Write the version.py file. This requires installation from the repo directly.
githash = (
    subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=here).decode().strip()
)
if subprocess.check_output(["git", "diff"], cwd=here).decode().strip():
    githash = githash + "-mod"
with open(here / "broccoli/version.py", "w") as version_file:
    version_file.write(f'BROCCOLI_GITHASH = "{githash}"\n')

setup(
    name="broccoli",
    version="0.1.0",
    description="Rather Ordinary Computing Cluster",
    # Note: this will only work if 'README.md' is present in your MANIFEST.in file!
    long_description="\n" + (here / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Simon Bowly",
    author_email="simon.bowly@gmail.com",
    python_requires=">=3.7.0",
    url="simonbowly/broccoli",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    entry_points={
        "console_scripts": [
            "broccoli-node=broccoli.node:cli",
            "broccoli-update=broccoli.update:update",
        ]
    },
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
