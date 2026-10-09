# Contributing to Orphan Repurpose

Thank you for your interest in contributing! This document explains how to submit bug reports, suggest features, and open pull requests.

---

## Table of Contents

- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Opening Pull Requests](#opening-pull-requests)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)

---

## Reporting Bugs

1. **Check existing issues** — Search the issue tracker to see if the bug has already been reported.
2. **Open a new issue** — Use the "Bug Report" template and include:
   - A clear, descriptive title
   - Steps to reproduce the problem
   - Expected vs. actual behavior
   - Your environment (OS, Python version, relevant dependencies)
   - Error messages or stack traces (use code blocks)
   - A minimal reproducible example if possible

## Suggesting Features

1. **Search first** — Check if a similar feature has already been proposed.
2. **Open a feature request** — Use the "Feature Request" template and describe:
   - The problem you're trying to solve
   - Your proposed solution
   - Any alternative approaches you've considered
   - Willingness to help implement it

## Opening Pull Requests

1. **Fork the repository** and create a new branch from `main`.
2. **Make your changes** — Keep changes focused; one concern per PR.
3. **Write or update tests** — All new functionality must include tests.
4. **Update documentation** — If your change affects usage, update the relevant docs.
5. **Run the test suite** — Ensure all tests pass before submitting.
6. **Open the PR** — Use the pull request template and provide:
   - A clear description of what the PR does and why
   - Reference to any related issues (e.g., `Closes #123`)
   - Screenshots or examples if applicable

### PR Review Process

- A maintainer will review your PR within a few days.
- You may be asked to make changes — this is normal and part of the process.
- Once approved, your PR will be merged by a maintainer.

## Development Setup

```bash
git clone https://github.com/your-org/orphan-repurpose.git
cd orphan-repurpose
pip install -e ".[dev]"
```

Run tests with:

```bash
make test
```

## Code Style

- Follow PEP 8 for Python code.
- Use meaningful variable and function names.
- Add docstrings to public functions and classes.
- Keep functions small and focused on a single responsibility.

## Commit Messages

- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
- Limit the first line to 72 characters or less.
- Reference issues and pull requests where relevant.

---

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
