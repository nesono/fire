#!/usr/bin/env python3
"""Tests proving dynamic models match static RequirementMetadata behaviour."""

import pytest
from pydantic import ValidationError

from fire.starlark.dynamic_requirement_model import (
    build_models_from_config,
    model_for_suffix,
)
from fire.starlark.requirement_models import (
    RequirementMetadata,
    RegulatoryRequirementMetadata,
)


@pytest.fixture()
def models(default_config):
    return build_models_from_config(default_config)


# ---------------------------------------------------------------------------
# Basic construction
# ---------------------------------------------------------------------------


class TestBuildModels:
    def test_builds_all_document_types(self, default_config, models):
        assert set(models.keys()) == set(default_config.document_types.keys())

    def test_model_for_suffix_sysreq(self, default_config, models):
        m = model_for_suffix(default_config, models, "some/path/req.sysreq.md")
        assert m is not None
        assert "sysreq" in m.__name__.lower()

    def test_model_for_suffix_regreq(self, default_config, models):
        m = model_for_suffix(default_config, models, "regulations.regreq.md")
        assert m is not None
        assert "regreq" in m.__name__.lower()

    def test_model_for_suffix_unknown(self, default_config, models):
        assert model_for_suffix(default_config, models, "notes.txt") is None


# ---------------------------------------------------------------------------
# Equivalence: valid inputs accepted by both static and dynamic models
# ---------------------------------------------------------------------------

_VALID_SYSREQ = {
    "id": "REQ-BRK-001",
    "sil": "ASIL-D",
    "sec": True,
    "version": 1,
}

_VALID_SYSREQ_WITH_PARENT = {
    "id": "REQ-BRK-002",
    "sil": "ASIL-B",
    "sec": False,
    "version": 2,
    "parent": ["[REQ-BRK-001](/braking.sysreq.md?version=1#REQ-BRK-001)"],
}

_VALID_SYSREQ_TODO_SIL = {
    "id": "REQ-BRK-003",
    "sil": "TODO(JIRA-42)",
    "sec": "TODO(JIRA-43)",
    "version": 1,
}

_VALID_REGREQ_MINIMAL = {
    "id": "REG-001",
    "version": 3,
}

_VALID_REGREQ_FULL = {
    "id": "REG-002",
    "sil": "SIL-2",
    "sec": True,
    "version": 1,
}


class TestSysreqEquivalence:
    """Dynamic sysreq model must accept/reject the same inputs as RequirementMetadata."""

    @pytest.mark.parametrize(
        "data",
        [_VALID_SYSREQ, _VALID_SYSREQ_WITH_PARENT, _VALID_SYSREQ_TODO_SIL],
        ids=["basic", "with_parent", "todo_fields"],
    )
    def test_accepts_valid(self, models, data):
        static = RequirementMetadata.model_validate(data)
        dynamic = models["sysreq"].model_validate(data)
        assert dynamic.id == static.id
        assert dynamic.version == static.version

    def test_rejects_extra_field(self, models):
        data = {**_VALID_SYSREQ, "extra": "nope"}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_missing_sil(self, models):
        data = {"id": "REQ-001", "sec": True, "version": 1}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_bad_sil(self, models):
        data = {**_VALID_SYSREQ, "sil": "INVALID"}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_bad_sec(self, models):
        data = {**_VALID_SYSREQ, "sec": "maybe"}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_zero_version(self, models):
        data = {**_VALID_SYSREQ, "version": 0}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_float_version(self, models):
        data = {**_VALID_SYSREQ, "version": 1.5}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_bad_parent_link(self, models):
        data = {**_VALID_SYSREQ, "parent": ["not a link"]}
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)

    def test_rejects_relative_parent_path(self, models):
        data = {
            **_VALID_SYSREQ,
            "parent": ["[REQ-001](relative.sysreq.md?version=1#REQ-001)"],
        }
        with pytest.raises(ValidationError):
            RequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["sysreq"].model_validate(data)


class TestRegreqEquivalence:
    """Dynamic regreq model must accept/reject the same inputs as RegulatoryRequirementMetadata."""

    @pytest.mark.parametrize(
        "data",
        [_VALID_REGREQ_MINIMAL, _VALID_REGREQ_FULL],
        ids=["minimal", "full"],
    )
    def test_accepts_valid(self, models, data):
        static = RegulatoryRequirementMetadata.model_validate(data)
        dynamic = models["regreq"].model_validate(data)
        assert dynamic.id == static.id
        assert dynamic.version == static.version

    def test_sil_sec_default_to_none(self, models):
        static = RegulatoryRequirementMetadata.model_validate(_VALID_REGREQ_MINIMAL)
        dynamic = models["regreq"].model_validate(_VALID_REGREQ_MINIMAL)
        assert static.sil is None
        assert dynamic.sil is None
        assert static.sec is None
        assert dynamic.sec is None

    def test_rejects_extra_field(self, models):
        data = {**_VALID_REGREQ_MINIMAL, "extra": "nope"}
        with pytest.raises(ValidationError):
            RegulatoryRequirementMetadata.model_validate(data)
        with pytest.raises(ValidationError):
            models["regreq"].model_validate(data)


# ---------------------------------------------------------------------------
# PL-* values (new in design)
# ---------------------------------------------------------------------------


class TestNewSilValues:
    def test_pl_values_accepted(self, models):
        for pl in ("PL-a", "PL-b", "PL-c", "PL-d"):
            data = {**_VALID_SYSREQ, "sil": pl}
            result = models["sysreq"].model_validate(data)
            assert result.sil == pl
