# Contributing to Arbitrage Bot

Thank you for your interest in contributing to the Arbitrage Bot project! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/arbitrage-bot.git
   cd arbitrage-bot
   ```

2. **Install Poetry**
   ```bash
   # Windows (PowerShell)
   pip install poetry

   # Linux/macOS
   pip install poetry
   ```

3. **Install Dependencies**
   ```bash
   poetry install
   ```

4. **Set Up Pre-commit Hooks**
   ```bash
   poetry run pre-commit install
   ```

## Development Workflow

1. **Create a New Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the code style guidelines
   - Write tests for new functionality
   - Update documentation as needed

3. **Run Tests**
   ```bash
   poetry run pytest
   ```

4. **Format Code**
   ```bash
   poetry run black .
   poetry run isort .
   ```

5. **Type Checking**
   ```bash
   poetry run mypy .
   ```

6. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Write docstrings for all functions and classes
- Keep functions small and focused
- Use meaningful variable and function names

## Testing Guidelines

- Write unit tests for all new functionality
- Maintain or improve test coverage
- Test edge cases and error conditions
- Use pytest fixtures for common setup

## Documentation

- Update README.md for significant changes
- Add docstrings to new functions and classes
- Update API documentation if needed
- Include examples for new features

## Adding Dependencies

1. **Production Dependencies**
   ```bash
   poetry add package-name
   ```

2. **Development Dependencies**
   ```bash
   poetry add --group dev package-name
   ```

3. **Update pyproject.toml**
   - Ensure version constraints are appropriate
   - Add any necessary configuration

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the documentation with any new features
3. Ensure all tests pass
4. Ensure code is properly formatted
5. Ensure type checking passes
6. The PR will be merged once you have the sign-off of at least one other developer

## Questions and Support

If you have any questions or need help, please:
1. Check the existing documentation
2. Search existing issues
3. Create a new issue if needed

Thank you for contributing! 