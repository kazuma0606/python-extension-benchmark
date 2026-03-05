"""
Setup script for Julia extension
"""

from setuptools import setup, find_packages

setup(
    name="julia_ext",
    version="1.0.0",
    description="Julia extension for Python benchmark system",
    packages=find_packages(),
    install_requires=[
        "julia>=0.6.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)