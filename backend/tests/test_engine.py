"""Tests for the anonymization engine (engine.py)."""

import pytest

from app.services.engine import generate_mappings


class TestDeterminism:
    """R28: Same project salt + column + value = same output."""

    def test_same_inputs_same_output(self):
        salt = "project-abc-123"
        col = "vendor_name"
        values = ["Walmart", "Target", "Costco"]

        result1 = generate_mappings(values, "fake", col, salt, "name")
        result2 = generate_mappings(values, "fake", col, salt, "name")

        assert result1 == result2

    def test_deterministic_across_calls(self):
        """Multiple calls produce identical mappings."""
        salt = "stable-salt-xyz"
        col = "email"
        values = ["user@example.com", "admin@test.org"]

        results = [
            generate_mappings(values, "fake", col, salt, "email")
            for _ in range(5)
        ]

        for r in results[1:]:
            assert r == results[0]


class TestCrossProjectIsolation:
    """R29: Different project salts = different outputs."""

    def test_different_salt_different_output(self):
        col = "vendor_name"
        values = ["Walmart", "Target"]

        result_a = generate_mappings(values, "fake", col, "salt-project-A", "name")
        result_b = generate_mappings(values, "fake", col, "salt-project-B", "name")

        # At least one mapping must differ
        assert result_a != result_b


class TestPassthroughStrategy:
    def test_returns_original_unchanged(self):
        values = ["keep_this", "and_this", "also_this"]
        result = generate_mappings(values, "passthrough", "col", "salt")

        for v in values:
            assert result[v] == v

    def test_all_values_present(self):
        values = ["a", "b", "c"]
        result = generate_mappings(values, "passthrough", "col", "salt")
        assert len(result) == 3


class TestDropStrategy:
    def test_returns_empty_dict(self):
        values = ["secret1", "secret2", "secret3"]
        result = generate_mappings(values, "drop", "col", "salt")
        assert result == {}


class TestHashStrategy:
    def test_consistent_12_char_hex(self):
        values = ["value1", "value2"]
        result = generate_mappings(values, "hash", "col", "salt123")

        for v in values:
            hashed = result[v]
            assert len(hashed) == 12
            # All hex characters
            assert all(c in "0123456789abcdef" for c in hashed)

    def test_hash_deterministic(self):
        values = ["test"]
        r1 = generate_mappings(values, "hash", "col", "salt")
        r2 = generate_mappings(values, "hash", "col", "salt")
        assert r1 == r2

    def test_hash_different_salts_differ(self):
        values = ["test"]
        r1 = generate_mappings(values, "hash", "col", "salt-A")
        r2 = generate_mappings(values, "hash", "col", "salt-B")
        assert r1["test"] != r2["test"]


class TestFakeStrategy:
    def test_name_type_returns_plausible_name(self):
        values = ["Walmart Inc", "Target Corp"]
        result = generate_mappings(values, "fake", "store", "salt", "name")

        for v in values:
            # Should be a non-empty string, not the original
            assert result[v] != v
            assert len(result[v]) > 0

    def test_email_type_returns_email_format(self):
        values = ["user@example.com"]
        result = generate_mappings(values, "fake", "email_col", "salt", "email")

        generated = result["user@example.com"]
        assert "@" in generated
        assert "." in generated.split("@")[1]

    def test_phone_type_returns_phone_format(self):
        values = ["555-123-4567"]
        result = generate_mappings(values, "fake", "phone_col", "salt", "phone")

        generated = result["555-123-4567"]
        # Should match XXX-XXX-XXXX pattern
        parts = generated.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 3
        assert len(parts[1]) == 3
        assert len(parts[2]) == 4


class TestSingleValue:
    def test_single_unique_value_one_entry_mapping(self):
        values = ["only_one"]
        result = generate_mappings(values, "fake", "col", "salt", "generic_string")
        assert len(result) == 1
        assert "only_one" in result


class TestFormatPreserve:
    def test_sku_format_preserved(self):
        values = ["WM-8842-A", "TG-1156-C"]
        result = generate_mappings(
            values, "format-preserve", "sku_col", "salt", "sku"
        )

        for v in values:
            generated = result[v]
            # Should match pattern: 2 alpha, dash, 4 digit, dash, 1 alpha
            assert len(generated) == len(v)
            assert generated[2] == "-"
            assert generated[7] == "-"
            assert generated[0:2].isalpha()
            assert generated[3:7].isdigit()
            assert generated[8].isalpha()
