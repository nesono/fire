"""Tests for unit suffix normalization."""

import sys

import pytest

from fire.starlark.unit_suffix import normalize_unit_suffix, unsupported_characters


class TestNormalizeUnitSuffix:
    @pytest.mark.parametrize(
        "unit, expected",
        [
            ("", ""),
            ("1", ""),
            ("dimensionless", ""),
            ("m", "m"),
            ("m/s", "mps"),
            ("m/s^2", "mps2"),
            ("kg/m^3", "kgpm3"),
            ("N·m", "nm"),
            ("m s", "ms"),
        ],
    )
    def test_ascii_units(self, unit, expected):
        assert normalize_unit_suffix(unit) == expected

    @pytest.mark.parametrize(
        "unit, expected",
        [
            ("°C", "degc"),
            ("°F", "degf"),
            ("°/s", "degps"),
            ("m/s²", "mps2"),
            ("m³", "m3"),
            ("%", "percent"),
            ("‰", "permille"),
            ("\u00b5m", "um"),
            ("\u03bcm", "um"),
            ("\u03a9", "ohm"),
            ("\u2126", "ohm"),
            ("dB(A)", "dba"),
        ],
    )
    def test_symbols_are_mapped(self, unit, expected):
        assert normalize_unit_suffix(unit) == expected


class TestUnsupportedCharacters:
    @pytest.mark.parametrize(
        "unit", ["m/s", "°C", "m/s²", "%", "µm", "dB(A)", "N·m", "1", ""]
    )
    def test_supported_units(self, unit):
        assert unsupported_characters(unit) == []

    @pytest.mark.parametrize(
        "unit, expected",
        [
            ("m.s", ["."]),
            ("m\nint x;", ["\n", ";"]),
            ("é", ["é"]),
            ("m,s,s", [","]),
            ("m'", ["'"]),
        ],
    )
    def test_unsupported_units(self, unit, expected):
        assert unsupported_characters(unit) == expected


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
