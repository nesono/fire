#!/usr/bin/env python3
"""Parity between the build-time validators and the editor diagnostics.

The failure-test fixtures under ``fire/starlark/failure_test`` and the examples
are run through both the build validators and the language server. Every
fixture is classified in ``_EXPECTATIONS``, so a fixture added for a new build
rule fails ``test_every_fixture_is_classified`` until the editor counterpart
exists, and ``test_every_rule_code_is_covered`` does the same the other way
round for a new editor rule.

Intentional divergences, each pinned by a test below:

* Requirement links without ``?version=N`` and links to a future requirement
  version are warnings in the editor; the build accepts them.
* ``[@x](<TODO(KEY-1)>)`` style links are not flagged by the editor.
* The editor works on one document. It does not know a target's ``deps``,
  duplicate IDs across files or release readiness (``_BUILD_ONLY``).
* Plain ``.md`` fixtures are not analyzed by the language server, so the test
  passes the model of the sysreq document type explicitly.
"""

from __future__ import annotations

import atexit
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from fire.lsp.diagnostic import Diagnostic, Severity
from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.parameter_diagnostics import diagnose_parameters
from fire.lsp.reference_diagnostics import ReferenceChecker
from fire.lsp.workspace import Workspace
from fire.starlark.config_models import load_config
from fire.starlark.dynamic_requirement_model import (
    build_models_from_config,
    model_for_suffix,
)
from fire.starlark.validate_cross_references import (
    validate_requirement_file,
    validate_unique_requirement_ids,
)
from fire.starlark.validate_parameters import validate_parameters

_FAILURE_TESTS = "fire/starlark/failure_test"
_FIXTURE_SUFFIXES = (".md", ".yaml")


def _copy_fixtures() -> Path:
    """Copy the fixtures into a scratch workspace.

    Under Bazel the fixtures are symlinks into the source tree, which the
    workspace rejects as links that leave its root.
    """
    source = Path(__file__).absolute().parents[2]
    root = Path(tempfile.mkdtemp(prefix="fire-parity-"))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    for directory in (_FAILURE_TESTS, "examples"):
        shutil.copytree(source / directory, root / directory, symlinks=False)
    return root


_ROOT = _copy_fixtures()
_CONFIG = load_config()
_MODELS = build_models_from_config(_CONFIG)
_SUFFIXES = tuple(d.suffix for d in _CONFIG.document_types.values())

ERROR = Severity.ERROR
WARNING = Severity.WARNING


@dataclass(frozen=True)
class Expect:
    """What the editor reports for a fixture.

    *build_fails* is whether the build validators reject the fixture. *editor*
    lists the ``(severity, code)`` pairs that must all be present; for a
    fixture the build accepts, ``()`` means no diagnostics at all.
    """

    build_fails: bool
    editor: tuple[tuple[Severity, str], ...] = ()


VALID = Expect(build_fails=False)


def _fails(code: str, severity: Severity = ERROR) -> Expect:
    return Expect(build_fails=True, editor=((severity, code),))


# Fixtures the build rejects for reasons the editor cannot see. The editor is
# pinned to the errors it reports instead, so closing a gap fails the test and
# asks for an update.
_BUILD_ONLY = {
    "duplicate_ids/first.sysreq.md": "ID duplicated in another file of the target",
    "duplicate_ids/second.sysreq.md": "ID duplicated in another file of the target",
    "dependency_failures/missing_req_dep.md": "link target not in the target's deps",
    "dependency_failures/missing_param_dep.md": "link target not in the target's deps",
}
_SHARED_ID_TARGET = ("duplicate_ids/first.sysreq.md", "duplicate_ids/second.sysreq.md")

# Rule codes the build has no counterpart for.
_EDITOR_ONLY = {
    "FIRE016": "undefined reference-style link label; the build does not parse them",
}

_EXPECTATIONS: dict[str, Expect] = {
    "bare_todo/bare_todo.md": _fails("FIRE004"),
    "bare_todo/todo_bad_format.md": _fails("FIRE004"),
    "dependency_failures/base_requirement.md": VALID,
    "duplicate_ids/twice.sysreq.md": _fails("FIRE002"),
    "invalid_metadata/invalid_dal.md": _fails("FIRE005"),
    "invalid_metadata/invalid_sec.md": _fails("FIRE005"),
    "invalid_metadata/invalid_sil.md": _fails("FIRE005"),
    "invalid_metadata/invalid_version_negative.md": _fails("FIRE005"),
    "invalid_metadata/invalid_version_zero.md": _fails("FIRE005"),
    "missing_child/orphan.sysreq.md": VALID,
    "missing_fields/missing_all.md": _fails("FIRE003"),
    "missing_fields/missing_sec.md": _fails("FIRE006"),
    "missing_fields/missing_sil.md": _fails("FIRE006"),
    "missing_fields/missing_version.md": _fails("FIRE006"),
    "non_conformant_heading/heading_with_title.sysreq.md": _fails("FIRE001"),
    "non_conformant_heading/lowercase_heading.sysreq.md": _fails("FIRE001"),
    "relative_paths/base_requirement.md": VALID,
    "relative_paths/non_absolute_param.md": _fails("FIRE009"),
    "relative_paths/non_absolute_parent.md": _fails("FIRE008"),
    "relative_paths/non_absolute_reference.md": _fails("FIRE009"),
    "source_traceability/test_requirements.sysreq.md": VALID,
    "unknown_parameter/suffix_of_other_parameter.md": _fails("FIRE013"),
    "unknown_parameter/version_not_declared.md": _fails("FIRE013"),
    "version_mismatch/base_requirement_v2.sysreq.md": VALID,
    "version_mismatch/test_param_version_mismatch.md": Expect(
        build_fails=False, editor=((WARNING, "FIRE015"),)
    ),
    "version_mismatch/test_param_version_mismatch_error.md": _fails("FIRE014"),
    "version_mismatch/test_version_mismatch.sysreq.md": Expect(
        build_fails=False, editor=((WARNING, "FIRE015"),)
    ),
    "non_finite_values/scalar_infinity.yaml": _fails("FIRE018"),
    "non_finite_values/table_nan.yaml": _fails("FIRE018"),
    "parameter_version/test_params.yaml": VALID,
    "table_row_shape/long_row.yaml": _fails("FIRE018"),
    "table_row_shape/short_row.yaml": _fails("FIRE018"),
    "too_many_versions/test_params.yaml": _fails("FIRE018"),
    "unit_identifiers/identifier_collision.yaml": _fails("FIRE018"),
    "unit_identifiers/unsupported_unit.yaml": _fails("FIRE018"),
    "unknown_parameter/test_params.yaml": VALID,
    "version_mismatch/test_params_v2.yaml": VALID,
    "relative_paths/test_params.yaml": VALID,
}
_EXPECTATIONS["duplicate_ids/first.sysreq.md"] = Expect(build_fails=True)
_EXPECTATIONS["duplicate_ids/second.sysreq.md"] = Expect(build_fails=True)
_EXPECTATIONS["dependency_failures/missing_req_dep.md"] = Expect(build_fails=True)
# The editor rejects this one too, but because the link has no version and
# points at a .bzl file, not because of the undeclared dependency.
_EXPECTATIONS["dependency_failures/missing_param_dep.md"] = Expect(
    build_fails=True, editor=((ERROR, "FIRE010"), (ERROR, "FIRE013"))
)


def _example_files() -> list[str]:
    examples = _ROOT / "examples"
    found = [
        p
        for p in examples.rglob("*")
        if p.suffix in _FIXTURE_SUFFIXES and p.name != "README.md"
    ]
    return sorted(str(p.relative_to(_ROOT)) for p in found)


def _failure_files() -> list[str]:
    base = _ROOT / _FAILURE_TESTS
    found = [p for p in base.rglob("*") if p.suffix in _FIXTURE_SUFFIXES]
    return sorted(str(p.relative_to(base)) for p in found)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _model_for(path: Path):
    return model_for_suffix(_CONFIG, _MODELS, str(path)) or _MODELS["sysreq"]


def _editor_diagnostics(path: Path, root: Path = _ROOT) -> list[Diagnostic]:
    if path.suffix == ".yaml":
        return diagnose_parameters(_read(path))
    references = ReferenceChecker(Workspace(root), _SUFFIXES)
    return diagnose_requirements(_read(path), _model_for(path), references)


def _build_errors(
    path: Path, declared: set[str], target: list[Path], root: Path = _ROOT
) -> list[str]:
    """Run the build validators the way a target with these files would.

    *declared* are the repository-relative paths in the target's srcs and deps,
    *target* the requirement files in its srcs.
    """
    if path.suffix == ".yaml":
        return validate_parameters(str(path))[1]
    errors = validate_requirement_file(str(path), str(root), declared, _CONFIG, _MODELS)
    return errors + validate_unique_requirement_ids([str(p) for p in target])


def _fixture_build_errors(relative: str) -> list[str]:
    path = _ROOT / _FAILURE_TESTS / relative
    package = path.parent
    if relative.startswith("dependency_failures/"):
        # The BUILD file declares no deps for these targets.
        declared = {str(path.relative_to(_ROOT))}
    else:
        declared = {
            str(p.relative_to(_ROOT))
            for p in package.iterdir()
            if p.suffix in _FIXTURE_SUFFIXES
        }
    target = [path]
    if relative in _SHARED_ID_TARGET:
        target = [_ROOT / _FAILURE_TESTS / name for name in _SHARED_ID_TARGET]
    return _build_errors(path, declared, target)


def _pairs(diagnostics: list[Diagnostic]) -> set[tuple[Severity, str]]:
    return {(d.severity, d.code) for d in diagnostics}


def _errors(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    return [d for d in diagnostics if d.severity == ERROR]


class TestFixtureParity:
    def test_every_fixture_is_classified(self):
        found = set(_failure_files())
        assert found, "no fixtures found; are the data dependencies missing?"
        assert found == set(_EXPECTATIONS)

    @pytest.mark.parametrize("relative", sorted(_EXPECTATIONS))
    def test_build_and_editor_agree(self, relative):
        expect = _EXPECTATIONS[relative]
        build_errors = _fixture_build_errors(relative)
        assert bool(build_errors) == expect.build_fails, build_errors
        diagnostics = _editor_diagnostics(_ROOT / _FAILURE_TESTS / relative)
        if relative in _BUILD_ONLY:
            assert _pairs(_errors(diagnostics)) == set(expect.editor)
        elif expect.editor:
            assert set(expect.editor) <= _pairs(diagnostics), diagnostics
            if not expect.build_fails:
                assert _errors(diagnostics) == []
        else:
            assert diagnostics == []

    @pytest.mark.parametrize("relative", _example_files())
    def test_examples_are_valid_in_both(self, relative):
        path = _ROOT / relative
        declared = set(_example_files())
        assert _build_errors(path, declared, [path]) == []
        # The examples keep a link to an older parameter version on purpose;
        # the build prints a warning for it, the editor reports FIRE015.
        assert _pairs(_editor_diagnostics(path)) <= {(WARNING, "FIRE015")}


_SYNTHETIC_ROOT_FILES = {
    "MODULE.bazel": "",
    "p.yaml": "x_v1:\n  value: 1\n  unit: m\n  description: d\n",
    "target.sysreq.md": "## REQ-B\n\nSIL: QM | Sec: false | Version: 2\n",
}
_HEADER = "## REQ-A\n\nSIL: QM | Sec: false | Version: 1"

# Rules without a failure-test fixture: a document the build rejects must get
# an error of the same code in the editor.
_INLINE_CASES = {
    "FIRE007": f"{_HEADER} | Colour: red\n",
    "FIRE010": f"{_HEADER}\n\n[@x](/p.yaml#x)\n",
    "FIRE011": f"{_HEADER}\n\n[@y](/p.yaml?version=1#x)\n",
    "FIRE012": f"{_HEADER}\n\n[@x](/gone.yaml?version=1#x)\n",
}


@pytest.fixture()
def workspace(tmp_path):
    for name, text in _SYNTHETIC_ROOT_FILES.items():
        (tmp_path / name).write_text(text)
    return tmp_path


def _both(workspace: Path, text: str) -> tuple[list[str], list[Diagnostic]]:
    doc = workspace / "doc.sysreq.md"
    doc.write_text(text)
    declared = {"doc.sysreq.md", "target.sysreq.md", "p.yaml"}
    build = _build_errors(doc, declared, [doc], workspace)
    return build, _editor_diagnostics(doc, workspace)


class TestRulesWithoutFixture:
    @pytest.mark.parametrize("code", sorted(_INLINE_CASES))
    def test_build_rejection_is_an_editor_error(self, workspace, code):
        build, editor = _both(workspace, _INLINE_CASES[code])
        assert build
        assert (ERROR, code) in _pairs(editor)

    def test_yaml_syntax_error(self, tmp_path):
        path = tmp_path / "broken.yaml"
        path.write_text("x_v1: [\n")
        assert validate_parameters(str(path))[1]
        assert (ERROR, "FIRE017") in _pairs(_editor_diagnostics(path))


class TestRuleCoverage:
    def test_every_rule_code_is_covered(self):
        defined: set[str] = set()
        for source in Path(__file__).parent.glob("*.py"):
            if not source.name.endswith("_test.py"):
                defined.update(re.findall(r'"(FIRE\d{3})"', _read(source)))
        defined.discard("FIRE999")
        tested = {code for e in _EXPECTATIONS.values() for _, code in e.editor}
        tested |= set(_INLINE_CASES) | {"FIRE017"}
        assert defined == tested | set(_EDITOR_ONLY)

    def test_editor_only_codes_are_not_also_tested(self):
        tested = {code for e in _EXPECTATIONS.values() for _, code in e.editor}
        assert tested.isdisjoint(_EDITOR_ONLY)


class TestIntentionalDivergences:
    def test_requirement_link_without_version_is_only_a_warning(self, workspace):
        body = f"{_HEADER}\n\n[REQ-B](/target.sysreq.md#REQ-B)\n"
        build, editor = _both(workspace, body)
        assert build == []
        assert _pairs(editor) == {(WARNING, "FIRE010")}

    def test_future_requirement_version_is_only_a_warning(self, workspace):
        body = f"{_HEADER}\n\n[REQ-B](/target.sysreq.md?version=3#REQ-B)\n"
        build, editor = _both(workspace, body)
        assert build == []
        assert _pairs(editor) == {(WARNING, "FIRE014")}

    def test_todo_url_is_not_flagged(self, workspace):
        build, editor = _both(workspace, f"{_HEADER}\n\n[@x](<TODO(KEY-1)>)\n")
        assert editor == []
        assert build != []  # the build still resolves it as a path


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
