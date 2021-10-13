#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name = "cachecat",
    version = read("VERSION"),
    license = "MIT",
    description = "Network communication via web cache poisoning",
    long_description = read("README.md"),
    long_description_content_type = "text/markdown",
    author = "johneiser",
    packages = find_packages(include=[
        "cachecat",
        "cachecat.*",
        ]),
    python_requires = ">=3.5.0",
    install_requires = [
        "requests",
        "shortuuid",
        ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production / Stable",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        ],
    entry_points = {
        "console_scripts" : [
            "cachecat=cachecat.__main__:main",
            ],
        },
    )

