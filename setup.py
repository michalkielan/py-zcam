#
# file setup.py
#
# SPDX-FileCopyrightText: (c) 2023 Michal Kielan
#
# SPDX-License-Identifier: MIT
#

""" Installation package. """

import io
from setuptools import setup, find_packages

with io.open("README.rst", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name="simpleadb",
    version="0.1.0",
    description="Python wrapper for zcam cameras network API.",
    long_description=long_description,
    author="Michal Kielan",
    author_email="michalkielan@protonmail.com",
    url="https://github.com/michalkielan/py-zcam",
    packages=find_packages(exclude=("tests", "docs")),
    python_requires=">3.0.0",
)
