# Contributing to LogForge

We love your input! We want to make contributing to LogForge as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Setup

1. Clone your fork of the repository
2. Install development dependencies:

```bash
pip install -e ".[dev]"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=logcore

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

## Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run these tools before submitting:

```bash
# Format code
black logcore tests examples
isort logcore tests examples

# Lint code
flake8 logcore tests examples

# Type check
mypy logcore
```

## Pull Request Process

1. Update the README.md with details of changes to the interface, if applicable
2. Update the version number in `pyproject.toml` and `__init__.py` if needed
3. The PR will be merged once you have the sign-off of a maintainer

## Any Contributions You Make Will Be Under the MIT License

When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.

## Report Bugs Using GitHub Issues

We use GitHub issues to track public bugs. Report a bug by opening a new issue.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
