# Autofix Guide

This document explains how to install and run automated tools to fix Python lint and formatting issues in the repository.

## Install autoflake and autopep8

Use the Python package manager to install the tools:

```bash
py -3 -m pip install autoflake autopep8
```

## Fix unused imports and formatting recursively

Run these commands from the repository root:

```bash
py -3 -m autoflake --in-place --remove-all-unused-imports --recursive antinode_norma tests
py -3 -m autopep8 --in-place --recursive --aggressive --aggressive antinode_norma tests
```

## Verify the result with flake8

Use the project's local lint command to confirm there are no remaining issues (excluding line-length checks):

```bash
py -3 -m flake8 antinode_norma/ tests/ --ignore=E501 --statistics
```

## Automate autofix before committing

Install `pre-commit` and enable the repository hooks once:

```bash
py -3 -m pip install pre-commit
pre-commit install
```

This installs a Git `pre-commit` hook that runs the configured fixers on changed Python files before every commit.

To run the hooks manually on the whole repository:

```bash
pre-commit run --all-files
```

If you want to make sure autofix tools are always applied before committing, use this workflow:

1. `git add .`
2. `pre-commit run --all-files`
3. Review any changes, then `git add` again.
4. `git commit`.

## Notes

- `autoflake` removes unused imports and unused variables where it is safe to do so.
- `autopep8` formats code to PEP 8 style and can also fix some whitespace and syntax issues.
- For any remaining lint failures, inspect the specific file and address the issue manually.
