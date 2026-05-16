"""Pattern-matching provider for SKUs and structured identifiers."""

import re
import string
from collections import Counter

from faker.providers import BaseProvider


def _char_class(c: str) -> str:
    """Classify a single character into a template slot type."""
    if c.isdigit():
        return "9"
    elif c.isalpha() and c.isupper():
        return "A"
    elif c.isalpha() and c.islower():
        return "a"
    else:
        # Literal delimiter (dash, underscore, dot, space, etc.)
        return c


def extract_pattern(value: str) -> str:
    """Convert a value into a character-class pattern template.

    Examples:
        "WM-8842-A"  -> "AA-9999-A"
        "abc-12"     -> "aaa-99"
        "TG_1156_C3" -> "AA_9999_A9"
    """
    return "".join(_char_class(c) for c in value)


def detect_dominant_pattern(values: list[str], threshold: float = 0.5) -> str | None:
    """Find the most common pattern among a list of values.

    Args:
        values: List of string values to analyze.
        threshold: Minimum fraction of values that must share the
                   dominant pattern. Returns None if not met.

    Returns:
        The dominant pattern string, or None if no pattern meets the threshold.
    """
    if not values:
        return None

    patterns = [extract_pattern(v) for v in values]
    counter = Counter(patterns)
    most_common_pattern, count = counter.most_common(1)[0]

    if count / len(values) >= threshold:
        return most_common_pattern
    return None


def generate_from_pattern(pattern: str, random_instance) -> str:
    """Generate a string matching the given pattern template.

    Args:
        pattern: Template string where 'A' = uppercase letter,
                 'a' = lowercase letter, '9' = digit, anything else = literal.
        random_instance: A Random instance for deterministic generation.
    """
    result = []
    for c in pattern:
        if c == "A":
            result.append(random_instance.choice(string.ascii_uppercase))
        elif c == "a":
            result.append(random_instance.choice(string.ascii_lowercase))
        elif c == "9":
            result.append(random_instance.choice(string.digits))
        else:
            # Literal character (delimiter)
            result.append(c)
    return "".join(result)


class PatternProvider(BaseProvider):
    """Generates fake values matching detected structural patterns."""

    def pattern_match(self, original: str) -> str:
        """Generate a fake value matching the pattern of the original.

        Extracts the character-class template from the original value,
        then fills each slot with a random character of the same class.
        """
        template = extract_pattern(original)
        return generate_from_pattern(template, self.generator.random)

    def pattern_match_batch(
        self, values: list[str], use_dominant: bool = True
    ) -> list[str]:
        """Generate fake values for a list, optionally using the dominant pattern.

        If use_dominant is True and a dominant pattern is found (>50% of values),
        all generated values will follow that pattern. Otherwise, each value
        gets its own pattern detected individually.
        """
        if use_dominant:
            dominant = detect_dominant_pattern(values)
            if dominant:
                return [
                    generate_from_pattern(dominant, self.generator.random)
                    for _ in values
                ]

        return [self.pattern_match(v) for v in values]
