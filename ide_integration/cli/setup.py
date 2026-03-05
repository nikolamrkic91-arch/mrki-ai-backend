#!/usr/bin/env python3
"""
Setup script for Mrki CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="mrki-cli",
    version="1.0.0",
    author="Mrki Team",
    author_email="team@mrki.dev",
    description="Command-line interface for Mrki AI Development Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mrki/mrki",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "requests>=2.28.0",
        "click>=8.0.0",
        "pydantic>=2.0.0",
        "watchdog>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "tui": [
            "textual>=0.41.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mrki=mrki_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
