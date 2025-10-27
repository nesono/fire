# Contributing to Fire

Thank you for your interest in contributing to Fire! This document provides guidelines and setup instructions for contributors.

## Development Setup

### Prerequisites

- Python 3.11 or later
- Bazel 7.0 or later
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fire.git
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

   This will automatically run code quality checks before each commit.

## Development Workflow

### Test-Driven Development (TDD)

Fire follows strict TDD practices:

1. **Write tests first** - Before implementing any feature, write tests
2. **Make tests pass** - Implement the minimum code needed
3. **Refactor** - Improve the code while keeping tests green
4. **Colocate tests** - Keep test files next to implementation files:
   ```
   fire/parameters/
   ├── validator.py          # Implementation
   └── validator_test.py     # Tests (same directory)
   ```

### Running Tests

```bash
# Run all tests
bazel test //...

# Run specific test suite
bazel test //fire/parameters:validator_test

# Run with verbose output
bazel test //fire/parameters:validator_test --test_output=all
```

### Code Quality Checks

Pre-commit hooks will automatically run when you commit. To manually run all checks:

```bash
# Run all pre-commit hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

### Code Style Guidelines

#### Python

- **Formatter**: Black (line length: 88)
- **Import sorting**: isort (Black-compatible profile)
- **Linting**: flake8
- **Type hints**: Use type hints; checked with mypy
- **Docstrings**: Google style

Example:

```python
"""Module docstring describing the module."""

from typing import Dict, List


def validate_parameter(param: Dict[str, Any]) -> None:
    """Validate a single parameter.

    Args:
        param: The parameter dictionary to validate

    Raises:
        ValidationError: If validation fails
    """
    pass
```

#### Bazel

- **Formatter**: Buildifier
- Keep dependencies sorted
- Use descriptive target names

Example:

```python
load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "validator",
    srcs = ["validator.py"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "validator_test",
    srcs = ["validator_test.py"],
    deps = [":validator"],
)
```

## Pre-commit Hooks

The following hooks are configured:

### General Checks
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML syntax
- **check-added-large-files**: Prevent large files (>1MB)
- **check-merge-conflict**: Detect merge conflict markers
- **check-case-conflict**: Detect case conflicts in filenames
- **mixed-line-ending**: Ensure consistent line endings

### Python Checks
- **black**: Auto-format Python code
- **isort**: Sort and organize imports
- **flake8**: Lint Python code
- **mypy**: Type checking
- **pydocstyle**: Check docstring style

### Bazel Checks
- **buildifier**: Format Bazel files
- **buildifier-lint**: Lint Bazel files

## Skipping Hooks (Use Sparingly)

If you absolutely need to skip pre-commit hooks:

```bash
git commit --no-verify -m "Your message"
```

**Note**: Only do this in exceptional circumstances. CI will still run these checks.

## Making Changes

### Adding New Features

1. **Create tests first**
   ```python
   # fire/parameters/new_feature_test.py
   def test_new_feature():
       # Test the new functionality
       pass
   ```

2. **Implement the feature**
   ```python
   # fire/parameters/new_feature.py
   def new_feature():
       # Implementation
       pass
   ```

3. **Run tests**
   ```bash
   bazel test //fire/parameters:new_feature_test
   ```

4. **Commit with descriptive message**
   ```bash
   git add fire/parameters/new_feature.py fire/parameters/new_feature_test.py
   git commit -m "Add new_feature for parameter validation"
   ```

### Updating Dependencies

1. Update `requirements.txt`
2. Update `requirements_lock.txt` if needed
3. Test that all builds still work:
   ```bash
   bazel test //...
   ```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following TDD

3. **Ensure all tests pass**
   ```bash
   bazel test //...
   ```

4. **Ensure pre-commit hooks pass**
   ```bash
   pre-commit run --all-files
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR should include**:
   - Clear description of changes
   - Tests for new functionality
   - Updated documentation if needed
   - All checks passing

## Continuous Integration

All pull requests must pass CI checks before merging. The CI pipeline runs:

### Pre-commit Checks
- Black (Python formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- pydocstyle (docstring style)
- Buildifier (Bazel formatting)
- General file checks

### Bazel Tests
- Runs on both Ubuntu and macOS
- All unit tests (`//fire/parameters:*_test`)
- Integration tests (`//examples:vehicle_params_test`)
- Build verification for all targets

### Integration Verification
- Verifies parameter validation
- Checks C++ code generation
- Validates generated headers

CI workflow is defined in `.github/workflows/ci.yaml`.

## Project Structure

```
fire/
├── fire/
│   ├── parameters/       # Core parameter logic
│   │   ├── *.py         # Implementation files
│   │   └── *_test.py    # Test files (colocated)
│   ├── rules/           # Bazel rule definitions
│   └── tools/           # Command-line tools
├── examples/            # Usage examples
├── docs/               # Documentation
├── .pre-commit-config.yaml  # Pre-commit configuration
├── CONTRIBUTING.md     # This file
└── README.md          # Project overview
```

## Troubleshooting

### Pre-commit is too slow

Pre-commit caches results. First run might be slow:

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Clean cache if needed
pre-commit clean
```

### Black and flake8 conflicts

Our configuration is set to avoid conflicts:
- Black line length: 88
- Flake8 configured to ignore E203, W503

### mypy errors

If mypy complains about missing imports:

```bash
# Add type stubs to additional_dependencies in .pre-commit-config.yaml
- id: mypy
  additional_dependencies: [types-PyYAML, types-<package>]
```

## Questions or Problems?

- Open an issue on GitHub
- Check existing issues and documentation
- Ask in pull request reviews

## Code of Conduct

- Be respectful and professional
- Follow TDD practices
- Write clear, tested code
- Document your changes
- Help review others' contributions

Thank you for contributing to Fire!
