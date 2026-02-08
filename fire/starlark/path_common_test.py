"""Tests for fire/starlark/path_common.py"""

from fire.starlark import path_common


class TestExtractVersionFromUrl:
    """Tests for extract_version_from_url function."""

    def test_url_with_version_and_fragment(self):
        url = "params.yaml?version=2#velocity"
        path, version = path_common.extract_version_from_url(url)
        assert path == "params.yaml#velocity"
        assert version == 2

    def test_url_with_version_only(self):
        url = "params.yaml?version=3"
        path, version = path_common.extract_version_from_url(url)
        assert path == "params.yaml"
        assert version == 3

    def test_url_with_fragment_only(self):
        url = "params.yaml#anchor"
        path, version = path_common.extract_version_from_url(url)
        assert path == "params.yaml#anchor"
        assert version is None

    def test_url_without_query_or_fragment(self):
        url = "params.yaml"
        path, version = path_common.extract_version_from_url(url)
        assert path == "params.yaml"
        assert version is None

    def test_url_with_multiple_query_params(self):
        url = "params.yaml?foo=bar&version=5&baz=qux#section"
        path, version = path_common.extract_version_from_url(url)
        assert path == "params.yaml#section"
        assert version == 5

    def test_url_with_non_numeric_version(self):
        url = "params.yaml?version=abc"
        path, version = path_common.extract_version_from_url(url)
        assert path == "params.yaml"
        assert version is None


class TestNormalizeRepoPath:
    """Tests for normalize_repo_path function."""

    def test_valid_absolute_path(self):
        is_valid, normalized, error = path_common.normalize_repo_path(
            "/path/to/file.yaml"
        )
        assert is_valid is True
        assert normalized == "path/to/file.yaml"
        assert error is None

    def test_valid_root_file(self):
        is_valid, normalized, error = path_common.normalize_repo_path("/file.yaml")
        assert is_valid is True
        assert normalized == "file.yaml"
        assert error is None

    def test_invalid_relative_path(self):
        is_valid, normalized, error = path_common.normalize_repo_path(
            "relative/path.yaml"
        )
        assert is_valid is False
        assert normalized == ""
        assert "repository-relative" in error
        assert "start with /" in error

    def test_empty_path(self):
        is_valid, normalized, error = path_common.normalize_repo_path("")
        assert is_valid is False
        assert normalized == ""
        assert error is not None


class TestValidateReferencePath:
    """Tests for validate_reference_path function."""

    def test_valid_path_with_extension(self):
        is_valid, normalized, error = path_common.validate_reference_path(
            "/params.yaml", ".yaml"
        )
        assert is_valid is True
        assert normalized == "params.yaml"
        assert error is None

    def test_valid_path_with_multiple_extensions(self):
        is_valid, normalized, error = path_common.validate_reference_path(
            "/doc.md", [".md", ".txt"]
        )
        assert is_valid is True
        assert normalized == "doc.md"
        assert error is None

    def test_invalid_extension(self):
        is_valid, normalized, error = path_common.validate_reference_path(
            "/params.json", ".yaml"
        )
        assert is_valid is False
        assert normalized == ""
        assert ".yaml" in error

    def test_invalid_path_format(self):
        is_valid, normalized, error = path_common.validate_reference_path(
            "relative.yaml", ".yaml"
        )
        assert is_valid is False
        assert "repository-relative" in error

    def test_no_extension_check(self):
        is_valid, normalized, error = path_common.validate_reference_path(
            "/any/file.ext", None
        )
        assert is_valid is True
        assert normalized == "any/file.ext"
        assert error is None

    def test_custom_ref_type_in_error(self):
        is_valid, normalized, error = path_common.validate_reference_path(
            "/file.txt", ".md", ref_type="requirement"
        )
        assert is_valid is False
        assert "Requirement path" in error
