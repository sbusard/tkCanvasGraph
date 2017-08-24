"""
Setup module for canvasGraph.
"""

from setuptools import setup, find_packages

with open("README.rst", "r") as readme:
    setup(
        name="canvasGraph",
        version="1.0",
        description=
        "A library to display and manipulate graphs on a tkinter canvas.",
        long_description=readme.read(),
        url="https://github.com/sbusard/canvasGraph",
        author="Simon Busard",
        author_email="simon.busard@gmail.com",
        license="MIT",
        classifiers=[
            "Intended Audience :: Developers",
            "Topic :: Utilities",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3"
        ],
        keywords="graph visualisation",
        packages=find_packages()
    )