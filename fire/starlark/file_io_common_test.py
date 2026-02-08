"""Tests for fire/starlark/file_io_common.py"""

from fire.starlark import file_io_common


class TestReadFileSafe:
    """Tests for read_file_safe function."""

    def test_read_existing_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        content, error = file_io_common.read_file_safe(str(test_file))
        assert content == "Hello, World!"
        assert error is None

    def test_read_nonexistent_file(self):
        content, error = file_io_common.read_file_safe("/nonexistent/file.txt")
        assert content is None
        assert "File not found" in error

    def test_read_empty_file(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        content, error = file_io_common.read_file_safe(str(test_file))
        assert content == ""
        assert error is None

    def test_read_multiline_file(self, tmp_path):
        test_file = tmp_path / "multi.txt"
        test_file.write_text("line1\nline2\nline3")

        content, error = file_io_common.read_file_safe(str(test_file))
        assert content == "line1\nline2\nline3"
        assert error is None


class TestLoadYamlSafe:
    """Tests for load_yaml_safe function."""

    def test_load_valid_yaml(self, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2")

        data, error = file_io_common.load_yaml_safe(str(yaml_file))
        assert data == {"key": "value", "list": ["item1", "item2"]}
        assert error is None

    def test_load_invalid_yaml(self, tmp_path):
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("key: value\n  bad indentation")

        data, error = file_io_common.load_yaml_safe(str(yaml_file))
        assert data is None
        assert "Invalid YAML syntax" in error

    def test_load_nonexistent_yaml(self):
        data, error = file_io_common.load_yaml_safe("/nonexistent.yaml")
        assert data is None
        assert "File not found" in error

    def test_load_empty_yaml(self, tmp_path):
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        data, error = file_io_common.load_yaml_safe(str(yaml_file))
        assert data is None
        assert error is None

    def test_load_yaml_with_numbers(self, tmp_path):
        yaml_file = tmp_path / "numbers.yaml"
        yaml_file.write_text("int: 42\nfloat: 3.14\nbool: true")

        data, error = file_io_common.load_yaml_safe(str(yaml_file))
        assert data == {"int": 42, "float": 3.14, "bool": True}
        assert error is None

    def test_load_yaml_with_nested_structure(self, tmp_path):
        yaml_file = tmp_path / "nested.yaml"
        yaml_file.write_text(
            """
root:
  level1:
    level2: value
    list:
      - a
      - b
"""
        )

        data, error = file_io_common.load_yaml_safe(str(yaml_file))
        assert data == {"root": {"level1": {"level2": "value", "list": ["a", "b"]}}}
        assert error is None
