#!/usr/bin/env python3
"""
Mrki - Full-Stack Development Environment
Setup script for package installation
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mrki-dev",
    version="1.0.0",
    author="Mrki Team",
    author_email="support@mrki.dev",
    description="Full-Stack Development Environment - Code generation, scaffolding, and DevOps automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mrki-team/mrki",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mrki=dev_env.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dev_env": [
            "templates/**/*",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords=[
        "code generator",
        "scaffolding",
        "full-stack",
        "web development",
        "api",
        "docker",
        "kubernetes",
        "ci/cd",
        "mern",
        "pern",
        "fastapi",
        "django",
        "react",
        "vue",
    ],
    project_urls={
        "Bug Reports": "https://github.com/mrki-team/mrki/issues",
        "Source": "https://github.com/mrki-team/mrki",
        "Documentation": "https://docs.mrki.dev",
    },
)
