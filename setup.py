"""Setup script for ASReview 5-Star package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="asreview-5star",
    version="0.1.0",
    author="ASReview Team",
    author_email="asreview@uu.nl",
    description="Enhanced systematic review tools with stopping rules, IRR, and meta-analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/asreview/asreview-5star",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "pydantic>=2.0.0",
        ],
        "dashboard": [
            "streamlit>=1.25.0",
            "plotly>=5.15.0",
        ],
        "all": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "pydantic>=2.0.0",
            "streamlit>=1.25.0",
            "plotly>=5.15.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "asreview-5star=asreview_5star.cli:main",
        ],
    },
)
