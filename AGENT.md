# AGENTS Guidelines for This Repository

This repository contains a Bazel project that provides a Bzlmod to be consumed
by other repositories. The repository uses Python and Starlark rules for the
business logic. Whatever is possible to execute in Starlark, we implement in
Starlark and the rest is using Python.

## Coding

Always write in TDD style. Write a small test first, make it fail, make it
succeed, refactor.

Always prefer small changes to big changes. Don't create comments unless they
provide semantics that are not obvious from the code.

Try to keep functions small (up to a dozen lines) and make proper use of
private functions if they are not needed outside of the module, the benefit is,
that they won't need documentation.

Use type hints in Python, and make sure that the code always supports all
supported Python version (as given in `.github/workflows/ci.yaml`)

Always use imports relative to the repository root, for instance for importing
from a file residing at `fire/starlark/validate_parameters.py`, the import
would look like:

```python
import fire.starlark.validate_parameters
```

Write Pythonic code.

## Pre-Commit

Whenever changing the code, make sure that pre-commit still works.

Formatters used:

- Black
- Ruff
- Buildifier
- Mypy

Ensure not to add any secrets to the code, they will be detected by

- gitleaks
- detect-secrets

## Testing

Test files use a `_test.py` suffix and are colocated with their implementation.
Test framework is pytest.
Always make sure that `bazel test //...` works when invoked from the repository
root.

Always make sure that integration tests are successful, which are run with
`run.sh` from the `integration_test` sub directory. The script `run.sh` takes
one parameter, which is the Python version to use

Also make sure that the failure tests are running successful, which are started
using `fire/starlark/failure_test/run_failure_tests.sh`.
