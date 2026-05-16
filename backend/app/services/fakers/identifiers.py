"""Identifier providers: UPC, phone, and email for Faker."""

from faker.providers import BaseProvider


def _compute_upc_check_digit(digits_11: list[int]) -> int:
    """Compute UPC-A check digit using GS1 mod-10 algorithm.

    Weights alternate 3, 1, 3, 1... starting at position 0.
    """
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits_11))
    return (10 - total % 10) % 10


def _is_valid_upc(code: str) -> bool:
    """Validate a 12-digit UPC-A code."""
    if len(code) != 12 or not code.isdigit():
        return False
    digits = [int(d) for d in code]
    expected = _compute_upc_check_digit(digits[:11])
    return digits[11] == expected


class UPCProvider(BaseProvider):
    """Generates valid or intentionally-invalid UPC-A codes."""

    def upc(self, valid: bool = True) -> str:
        """Generate a 12-digit UPC-A code.

        Args:
            valid: If True, generates a code with correct check digit.
                   If False, corrupts the check digit by +1 mod 10.
        """
        digits_11 = [self.random_int(0, 9) for _ in range(11)]
        check = _compute_upc_check_digit(digits_11)

        if valid:
            digits_11.append(check)
        else:
            # Corrupt check digit: shift by 1 so it's definitely wrong
            digits_11.append((check + 1) % 10)

        return "".join(str(d) for d in digits_11)

    def upc_batch(self, count: int, valid_rate: float = 1.0) -> list[str]:
        """Generate a batch of UPC codes with a given validity rate.

        Args:
            count: Number of codes to generate.
            valid_rate: Fraction of codes that should have valid check digits.
                        E.g., 0.92 means 92% valid, 8% invalid.
        """
        valid_count = int(count * valid_rate)
        codes = []
        for i in range(count):
            codes.append(self.upc(valid=(i < valid_count)))
        return codes


# Valid US area codes: 200-999 range, excluding 555 (reserved/fictional).
_VALID_AREA_CODE_RANGES = list(range(200, 555)) + list(range(556, 1000))


class PhoneProvider(BaseProvider):
    """Generates US-format phone numbers with valid area codes."""

    def us_phone(self) -> str:
        """Generate a US phone number in XXX-XXX-XXXX format.

        Area code is in 200-999 range, excluding 555.
        Exchange code is in 200-999 range.
        """
        area = self.random_element(_VALID_AREA_CODE_RANGES)
        # Exchange code: 200-999 (first digit 2-9)
        exchange = self.random_int(200, 999)
        subscriber = self.random_int(0, 9999)
        return f"{area:03d}-{exchange:03d}-{subscriber:04d}"


# Realistic email domains that look plausible without being real.
_EMAIL_DOMAINS = [
    "inbox.com", "mailbox.net", "postmail.org", "sendgrid.io",
    "fastmail.com", "proton.me", "outlook.com", "gmail.com",
    "yahoo.com", "icloud.com", "zoho.com", "aol.com",
    "hotmail.com", "live.com", "mail.com", "ymail.com",
    "gmx.com", "tutanota.com", "pm.me", "hey.com",
]

_EMAIL_FIRST_PARTS = [
    "james", "mary", "john", "patricia", "robert", "jennifer",
    "michael", "linda", "david", "elizabeth", "william", "barbara",
    "richard", "susan", "joseph", "jessica", "thomas", "sarah",
    "daniel", "karen", "matthew", "lisa", "anthony", "nancy",
    "mark", "betty", "donald", "margaret", "steven", "sandra",
    "paul", "ashley", "andrew", "dorothy", "joshua", "kimberly",
    "kenneth", "emily", "kevin", "donna", "brian", "michelle",
    "george", "carol", "timothy", "amanda", "ronald", "melissa",
]


class EmailProvider(BaseProvider):
    """Generates plausible email addresses."""

    def realistic_email(self) -> str:
        """Generate a plausible user@domain.com email address."""
        first = self.random_element(_EMAIL_FIRST_PARTS)
        # Add variety with numbers or dots
        separator = self.random_element([".", "_", ""])
        suffix = self.random_element(
            ["", str(self.random_int(1, 99)), str(self.random_int(100, 999))]
        )
        domain = self.random_element(_EMAIL_DOMAINS)

        if suffix:
            local = f"{first}{separator}{suffix}"
        else:
            # Sometimes add a last initial
            last_initial = self.random_element("abcdefghijklmnopqrstuvwxyz")
            local = f"{first}{separator}{last_initial}"

        return f"{local}@{domain}"
