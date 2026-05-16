"""Anonymization engine: maps original values to anonymized values.

Takes a column's unique values + confirmed strategy and returns a
mapping dict (original -> anonymized). Uses deterministic seeding
so the same project + column + value always produces the same output.
"""

import hashlib

from faker import Faker

from .fakers.identifiers import (
    EmailProvider,
    PhoneProvider,
    UPCProvider,
    _is_valid_upc,
)
from .fakers.patterns import PatternProvider, detect_dominant_pattern, extract_pattern
from .fakers.retail import RetailProvider


def _make_seeded_faker(seed: int) -> Faker:
    """Create a Faker instance seeded for deterministic output."""
    fake = Faker()
    Faker.seed(seed)
    fake.seed_instance(seed)
    fake.add_provider(RetailProvider)
    fake.add_provider(UPCProvider)
    fake.add_provider(PhoneProvider)
    fake.add_provider(EmailProvider)
    fake.add_provider(PatternProvider)
    return fake


def _compute_seed(project_salt: str, column_name: str, value: str) -> int:
    """Deterministic seed from project salt + column + value."""
    raw = (project_salt + column_name + value).encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def _detect_upc_valid_rate(values: list[str]) -> float:
    """Detect what fraction of UPC values have valid check digits."""
    if not values:
        return 1.0
    valid_count = sum(1 for v in values if _is_valid_upc(v.strip()))
    return valid_count / len(values)


def _generate_fake(value: str, seed: int, detected_type: str) -> str:
    """Generate a fake value based on detected column type."""
    fake = _make_seeded_faker(seed)

    if detected_type == "name":
        return fake.retail_name()
    elif detected_type == "email":
        return fake.realistic_email()
    elif detected_type == "phone":
        return fake.us_phone()
    elif detected_type == "upc_gtin":
        return fake.upc(valid=True)
    elif detected_type == "sku":
        return fake.pattern_match(value)
    else:
        # Generic: generate a name-like string
        return fake.name()


def _generate_format_preserve(
    value: str,
    seed: int,
    detected_type: str,
    valid_rate: float = 1.0,
) -> str:
    """Generate a format-preserving fake value."""
    fake = _make_seeded_faker(seed)

    if detected_type == "upc_gtin":
        # Decide if this particular value should be valid or invalid
        # based on the column's overall validity rate
        should_be_valid = fake.random_int(1, 100) <= int(valid_rate * 100)
        return fake.upc(valid=should_be_valid)
    elif detected_type == "sku":
        return fake.pattern_match(value)
    else:
        # Fallback: pattern-based format preservation
        return fake.pattern_match(value)


def generate_mappings(
    unique_values: list[str],
    strategy: str,
    column_name: str,
    project_salt: str,
    detected_type: str = "generic_string",
) -> dict[str, str]:
    """Generate a mapping dict from original values to anonymized values.

    Args:
        unique_values: List of unique values found in the column.
        strategy: One of "passthrough", "drop", "hash", "fake", "format-preserve".
        column_name: Name of the column being anonymized.
        project_salt: Project-specific salt for deterministic seeding.
        detected_type: The detected data type (e.g., "name", "email", "upc_gtin").

    Returns:
        Dict mapping original values to their anonymized replacements.
        For "drop" strategy, returns an empty dict.
    """
    if strategy == "drop":
        return {}

    if strategy == "passthrough":
        return {v: v for v in unique_values}

    # For UPC format-preserve, pre-compute the validity rate from the originals
    valid_rate = 1.0
    if strategy == "format-preserve" and detected_type == "upc_gtin":
        valid_rate = _detect_upc_valid_rate(unique_values)

    mappings: dict[str, str] = {}
    for value in unique_values:
        seed = _compute_seed(project_salt, column_name, value)

        if strategy == "hash":
            mappings[value] = hashlib.sha256(
                (project_salt + value).encode()
            ).hexdigest()[:12]
        elif strategy == "fake":
            mappings[value] = _generate_fake(value, seed, detected_type)
        elif strategy == "format-preserve":
            mappings[value] = _generate_format_preserve(
                value, seed, detected_type, valid_rate
            )

    return mappings
