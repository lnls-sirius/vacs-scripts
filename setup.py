#!/usr/bin/env python
from setuptools import setup

requirements = None
with open("requirements.txt", "r") as _f:
    requirements = _f.readlines()

setup(
    name="vacs_scripts",
    packages=["vacs_scripts"],
    include_package_data=True,
    install_requires=requirements,
    scripts=["scripts/sirius-hla-as-va-scripts.py"],
)
