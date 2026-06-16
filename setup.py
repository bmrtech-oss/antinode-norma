from setuptools import setup, find_packages

setup(
    name="antinode_norma",
    version="0.1.0",
    description="BDD feature file generator with INVEST quality gate - Antinode Labs",
    author="Antinode Labs",
    author_email="info@antinodelabs.com",
    url="https://antinodelabs.com/",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.23.0",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "mcp>=0.1.0",
        "jira>=3.4.0",
        "requests>=2.31.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "anorm = antinode_norma.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
)