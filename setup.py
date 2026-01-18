"""
Setup script for SDRIG SDK
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
else:
    requirements = [
        "scapy>=2.5.0",
        "cantools>=39.0.0",
        "python-can>=4.0.0",
    ]

setup(
    name="sdrig-sdk",
    version="0.1.0",
    author="SODA Validate",
    author_email="support@sodavalidate.com",
    description="Python SDK for SDRIG (Software-Defined Remote Interface Gateway)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/soda-auto/soda-validate-sdrig-sdk-py",
    project_urls={
        "Bug Tracker": "https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues",
        "Documentation": "https://github.com/soda-auto/soda-validate-sdrig-sdk-py",
        "Source Code": "https://github.com/soda-auto/soda-validate-sdrig-sdk-py",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
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
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "pylint>=2.15.0",
            "mypy>=0.990",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.dbc"],
    },
    keywords="sdrig can avtp automotive hardware testing",
    license="MIT",
)
