import hashlib

from faker import Faker

from .fakers.identifiers import (
    EmailProvider,
    PhoneProvider,
    UPCProvider,
    _is_valid_upc,
)
from .fakers.patterns import PatternProvider
from .fakers.retail import RetailProvider


def _make_faker_with_providers() -> Faker:
    fake = Faker()
    fake.add_provider(RetailProvider)
    fake.add_provider(UPCProvider)
    fake.add_provider(PhoneProvider)
    fake.add_provider(EmailProvider)
    fake.add_provider(PatternProvider)
    return fake


def _compute_seed(project_salt: str, column_name: str, value: str) -> int:
    raw = (project_salt + column_name + value).encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def _detect_upc_valid_rate(values: list[str]) -> float:
    if not values:
        return 1.0
    valid_count = sum(1 for v in values if _is_valid_upc(v.strip()))
    return valid_count / len(values)


def _generate_fake(fake: Faker, value: str, detected_type: str) -> str:
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
        return fake.name()


def _generate_format_preserve(
    fake: Faker,
    value: str,
    detected_type: str,
    valid_rate: float = 1.0,
) -> str:
    if detected_type == "upc_gtin":
        should_be_valid = fake.random_int(1, 100) <= int(valid_rate * 100)
        return fake.upc(valid=should_be_valid)
    elif detected_type == "sku":
        return fake.pattern_match(value)
    else:
        return fake.pattern_match(value)


def generate_mappings(
    unique_values: list[str],
    strategy: str,
    column_name: str,
    project_salt: str,
    detected_type: str = "generic_string",
) -> dict[str, str]:
    if strategy == "drop":
        return {}

    if strategy == "passthrough":
        return {v: v for v in unique_values}

    valid_rate = 1.0
    if strategy == "format-preserve" and detected_type == "upc_gtin":
        valid_rate = _detect_upc_valid_rate(unique_values)

    fake = _make_faker_with_providers()
    mappings: dict[str, str] = {}
    for value in unique_values:
        seed = _compute_seed(project_salt, column_name, value)
        fake.seed_instance(seed)

        if strategy == "hash":
            mappings[value] = hashlib.sha256(
                (project_salt + column_name + value).encode()
            ).hexdigest()[:12]
        elif strategy == "fake":
            mappings[value] = _generate_fake(fake, value, detected_type)
        elif strategy == "format-preserve":
            mappings[value] = _generate_format_preserve(
                fake, value, detected_type, valid_rate
            )

    return mappings
