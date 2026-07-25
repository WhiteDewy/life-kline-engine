# setup.py — 向后兼容；主配置在 pyproject.toml
from setuptools import setup, find_packages

setup(
    name="life-kline-engine",
    version="0.3.3",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "anyio>=4.0.0",
        "httpx>=0.27.0",
        "pydantic>=2.5.0",
        "numpy>=1.24",
        "pyswisseph>=2.10.3",
        "typing_extensions>=4.8.0",
    ],
)
