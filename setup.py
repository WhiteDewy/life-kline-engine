# setup.py
from setuptools import setup, find_packages

setup(
    name="life-kline-engine",
    version="0.3.3",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24",
    ],
)