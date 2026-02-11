# AGENTS Guidelines for This Repository

This repository contains a Bazel project that provides a Bzlmod to be consumed
by other repositories. The repository uses Python and Starlark rules for the
business logic. Whatever is possible to execute in Starlark, we implement in
Starlark and the rest is using Python.

## Git Usage

Never commit directly to the `main` branch, always ensure there is a branch
ready to create a (new) PR from.

## Coding

Import statements should be at the top of the file by default and only be added
within functions if they are particularly heavy and/or there is a strong case
to use lazy loading.

Always write in TDD style. Write a small test first, make it fail, make it
succeed, refactor. Please make sure to always go through these steps, don't
skip the making the test fail step, to ensure that the tests are actually run.

Always prefer small PRs to big PRs. Optimally not consisting of more than 10-50
lines of code with significant complexity. Optimize the PRs to be easy to
review, make them byte sized and keep the PR description concise. If the
feature is big, it's good practice to add small parts of code with their tests
that are not activated, yet.

Don't create comments unless they provide semantics that are not obvious from
the code. If you add comments, make sure they add information that is not
already obvious from the code, but rather explain the 'why' rather than the
'how'.

Try to keep functions small (up to 12 lines of code) and make proper use of
private functions if they are not needed outside of the module, the benefit is,
that they won't need documentation.

Use type hints in Python, and make sure that the code always supports all
supported Python version (as given in `.github/workflows/ci.yaml`). Use type
hints when they cannot be easily deduced (easily deduced is for instance, when
the objects are defined and assigned with a literal. Use the Final keyword when
it makes sense (e.g. for global const objects).

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

Please also ensure to use pytest and that there is a pytest.main() call at the
end of the test code - otherwise Bazel won't run the test.

Also run bazel testing both with --config=typecheck and without it.
The typecheck config checks code formatting with ty.

## Documentation

Always keep the documentation up to date. When changing the interfaces or
behavior, make sure that there is no contradicting documentation in the
repository.

Please keep the information to the points mentioned, no other information like
Test Results, "Benefits", etc.

## PR Format

Please use the following format as a blueprint for PR descriptions:

### Summary

Short summary of what changed with this PR. Focus on the 'what', not the 'why'.

### Implementation Summary

Summarize what was changed and what design choices were made and their
potential ramifications.

### Testing

Summarize what test strategy you used and what modalities you used (unit test,
integration tests, failure tests, etc.) and give a brief summary if what tests
you added and or modified.
