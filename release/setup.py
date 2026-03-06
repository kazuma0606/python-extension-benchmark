"""Setup script for Python Extension Benchmark Framework."""

from setuptools import setup, find_packages

setup(
    name="python-extension-benchmark",
    version="0.1.0",
    description="Benchmark framework for comparing Python extension implementations",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pytest>=7.4.0",
        "hypothesis>=6.82.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.4.0",
        ],
    },
)
