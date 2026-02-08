# Contributing to AquaWatch NRW

Thank you for your interest in contributing to AquaWatch NRW! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** and clone it locally
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

- **Python**: We use [Black](https://black.readthedocs.io/) for formatting and [Ruff](https://docs.astral.sh/ruff/) for linting
- **TypeScript**: Follow the ESLint configuration in the `dashboard/` directory
- Run linting before submitting:
  ```bash
  black --check src/ tests/
  ruff check src/ tests/
  ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py
```

### Commit Messages

Use clear, descriptive commit messages:
- `feat: add pressure threshold configuration`
- `fix: correct anomaly detection false positive rate`
- `docs: update deployment guide for Docker`
- `test: add unit tests for leak localizer`

## Pull Request Process

1. Update documentation if your change affects user-facing behavior
2. Add tests for new functionality
3. Ensure all tests pass and linting is clean
4. Update the README.md if needed
5. Submit a pull request with a clear description of the changes

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce for bugs
- Provide sensor data samples if relevant to the issue

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to providing a welcoming and inclusive experience for everyone.

## Questions?

- Technical: engineering@aquawatch.io
- General: partnerships@aquawatch.io
