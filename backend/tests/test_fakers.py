"""Tests for custom Faker providers."""

import re

import pytest
from faker import Faker

from app.services.fakers.identifiers import (
    EmailProvider,
    PhoneProvider,
    UPCProvider,
    _compute_upc_check_digit,
    _is_valid_upc,
)
from app.services.fakers.patterns import (
    PatternProvider,
    detect_dominant_pattern,
    extract_pattern,
    generate_from_pattern,
)
from app.services.fakers.retail import ALL_NAMES, RetailProvider


class TestUPCProvider:
    @pytest.fixture
    def fake(self):
        f = Faker()
        f.seed_instance(42)
        f.add_provider(UPCProvider)
        return f

    def test_generates_12_digits(self, fake):
        code = fake.upc(valid=True)
        assert len(code) == 12
        assert code.isdigit()

    def test_valid_check_digit(self, fake):
        for _ in range(50):
            code = fake.upc(valid=True)
            assert _is_valid_upc(code), f"Invalid UPC generated: {code}"

    def test_invalid_check_digit(self, fake):
        for _ in range(50):
            code = fake.upc(valid=False)
            assert not _is_valid_upc(code), f"Valid UPC when invalid expected: {code}"

    def test_batch_valid_rate(self, fake):
        """92 valid + 8 invalid originals -> output has ~8 invalid fakes."""
        batch = fake.upc_batch(count=100, valid_rate=0.92)
        assert len(batch) == 100

        valid_count = sum(1 for code in batch if _is_valid_upc(code))
        invalid_count = 100 - valid_count

        # Should be approximately 92 valid and 8 invalid
        assert valid_count == 92
        assert invalid_count == 8

    def test_check_digit_algorithm(self):
        # Known UPC: 012345678905
        digits_11 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
        check = _compute_upc_check_digit(digits_11)
        assert check == 5


class TestPhoneProvider:
    @pytest.fixture
    def fake(self):
        f = Faker()
        f.seed_instance(42)
        f.add_provider(PhoneProvider)
        return f

    def test_matches_pattern(self, fake):
        for _ in range(100):
            phone = fake.us_phone()
            assert re.match(r"^\d{3}-\d{3}-\d{4}$", phone), f"Bad format: {phone}"

    def test_valid_area_code(self, fake):
        for _ in range(100):
            phone = fake.us_phone()
            area = int(phone[:3])
            assert 200 <= area <= 999, f"Area code out of range: {area}"
            assert area != 555, f"Area code is 555: {phone}"

    def test_valid_exchange_code(self, fake):
        for _ in range(100):
            phone = fake.us_phone()
            exchange = int(phone[4:7])
            assert 200 <= exchange <= 999, f"Exchange code out of range: {exchange}"


class TestEmailProvider:
    @pytest.fixture
    def fake(self):
        f = Faker()
        f.seed_instance(42)
        f.add_provider(EmailProvider)
        return f

    def test_email_format(self, fake):
        email_re = re.compile(r"^[a-zA-Z0-9._]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        for _ in range(100):
            email = fake.realistic_email()
            assert email_re.match(email), f"Invalid email format: {email}"

    def test_has_at_sign_and_domain(self, fake):
        for _ in range(20):
            email = fake.realistic_email()
            assert "@" in email
            local, domain = email.split("@")
            assert len(local) > 0
            assert "." in domain


class TestPatternProvider:
    @pytest.fixture
    def fake(self):
        f = Faker()
        f.seed_instance(42)
        f.add_provider(PatternProvider)
        return f

    def test_extract_pattern_sku(self):
        assert extract_pattern("WM-8842-A") == "AA-9999-A"

    def test_extract_pattern_lowercase(self):
        assert extract_pattern("abc-12") == "aaa-99"

    def test_extract_pattern_mixed(self):
        assert extract_pattern("TG_1156_C3") == "AA_9999_A9"

    def test_extract_pattern_preserves_delimiters(self):
        assert extract_pattern("AB.123.XY") == "AA.999.AA"

    def test_generate_matches_sku_pattern(self, fake):
        """'WM-8842-A' -> detects 'AA-9999-A' pattern, generates matching fakes."""
        original = "WM-8842-A"
        generated = fake.pattern_match(original)

        assert len(generated) == len(original)
        assert generated[2] == "-"
        assert generated[7] == "-"
        assert generated[0].isupper() and generated[1].isupper()
        assert generated[3:7].isdigit()
        assert generated[8].isupper()

    def test_generate_preserves_structure(self, fake):
        original = "ABC-1234"
        generated = fake.pattern_match(original)

        assert len(generated) == 8
        assert generated[3] == "-"
        assert generated[:3].isalpha() and generated[:3].isupper()
        assert generated[4:].isdigit()

    def test_dominant_pattern_detection(self):
        # 80% "AA-9999-A" pattern, 20% "AAA-99"
        values = ["WM-8842-A"] * 80 + ["ABC-12"] * 20
        dominant = detect_dominant_pattern(values, threshold=0.5)
        assert dominant == "AA-9999-A"

    def test_dominant_pattern_mixed_lengths(self):
        """Mixed patterns: uses dominant when threshold met."""
        values = (
            ["WM-8842-A", "TG-1156-C", "CS-3301-B", "AB-9912-D"] * 20  # 80 x AA-9999-A
            + ["ABC-12", "DEF-34", "GHI-56", "JKL-78"] * 5  # 20 x AAA-99
        )
        dominant = detect_dominant_pattern(values, threshold=0.5)
        assert dominant == "AA-9999-A"

    def test_no_dominant_pattern_below_threshold(self):
        # 40% each of two patterns, neither meets 50% threshold
        values = ["AB-12"] * 40 + ["ABC-123"] * 40 + ["A-1"] * 20
        dominant = detect_dominant_pattern(values, threshold=0.5)
        # No single pattern has > 50%
        assert dominant is None

    def test_generate_from_pattern_deterministic(self):
        """Same seed produces same output."""
        import random

        r1 = random.Random(12345)
        r2 = random.Random(12345)

        result1 = generate_from_pattern("AA-9999-A", r1)
        result2 = generate_from_pattern("AA-9999-A", r2)
        assert result1 == result2


class TestRetailProvider:
    @pytest.fixture
    def fake(self):
        f = Faker()
        f.seed_instance(42)
        f.add_provider(RetailProvider)
        return f

    def test_returns_plausible_name(self, fake):
        """Names from the pool are plausible business names."""
        for _ in range(50):
            name = fake.retail_name()
            assert len(name) > 3
            # Should not look like "Company_47831"
            assert "_" not in name or "Co" in name
            assert name in ALL_NAMES

    def test_curated_pool_size(self):
        """Pool has approximately 200 names."""
        assert len(ALL_NAMES) >= 190
        assert len(ALL_NAMES) <= 210

    def test_name_with_number_format(self, fake):
        """Optional store number format: 'Name #123'."""
        found_with_number = False
        found_without_number = False

        for _ in range(200):
            name = fake.retail_name_with_number()
            if "#" in name:
                found_with_number = True
                # Format: "Name #NNN"
                base, num_part = name.rsplit(" #", 1)
                assert base in ALL_NAMES
                assert num_part.isdigit()
            else:
                found_without_number = True
                assert name in ALL_NAMES

        # Both variants should appear over 200 iterations
        assert found_with_number
        assert found_without_number

    def test_no_duplicates_in_pool(self):
        """All names in the curated pool are unique."""
        assert len(ALL_NAMES) == len(set(ALL_NAMES))
