"""Tests for fire/starlark/generate_code.py"""

import sys

import pytest

from fire.starlark.generate_code import normalize_unit_suffix


class TestNormalizeUnitSuffix:
    """Tests for normalize_unit_suffix function."""

    def test_empty_string_returns_empty(self):
        """Empty unit string returns empty suffix."""
        assert normalize_unit_suffix("") == ""

    def test_dimensionless_returns_empty(self):
        """'dimensionless' unit returns empty suffix."""
        assert normalize_unit_suffix("dimensionless") == ""

    def test_unit_one_returns_empty(self):
        """Unit '1' (dimensionless quantity) returns empty suffix."""
        assert normalize_unit_suffix("1") == ""

    def test_simple_unit(self):
        """Simple unit like 'm' returns as-is."""
        assert normalize_unit_suffix("m") == "m"

    def test_meters_per_second(self):
        """'m/s' converts to 'mps'."""
        assert normalize_unit_suffix("m/s") == "mps"

    def test_meters_per_second_squared(self):
        """'m/s^2' converts to 'mps2'."""
        assert normalize_unit_suffix("m/s^2") == "mps2"

    def test_radians_per_second(self):
        """'rad/s' converts to 'radps'."""
        assert normalize_unit_suffix("rad/s") == "radps"

    def test_cubic_meters(self):
        """'m^3' converts to 'm3'."""
        assert normalize_unit_suffix("m^3") == "m3"

    def test_kg_per_cubic_meter(self):
        """'kg/m^3' converts to 'kgpm3'."""
        assert normalize_unit_suffix("kg/m^3") == "kgpm3"

    def test_uppercase_dimensionless(self):
        """'DIMENSIONLESS' (uppercase) returns empty suffix."""
        assert normalize_unit_suffix("DIMENSIONLESS") == ""

    def test_mixed_case_dimensionless(self):
        """'Dimensionless' (mixed case) returns empty suffix."""
        assert normalize_unit_suffix("Dimensionless") == ""


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
