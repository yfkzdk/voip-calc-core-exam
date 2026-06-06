"""CountryCode value object. Encapsulates country calling code and base rate."""

import re
from dataclasses import dataclass
from decimal import Decimal

from .money import Money, CNY


class InvalidCountryCodeError(ValueError):
    """Country code format is invalid."""
    ...


@dataclass(frozen=True)
class CountryCode:
    """Country calling code value object.

    Format: + followed by digits (e.g., +86, +1).
    Base rate mapping for known codes; unknown codes get _DEFAULT_RATE.
    """

    code: str

    _PATTERN = re.compile(r"^\+\d+$")

    _BASE_RATES = {
        "+86": Decimal("0.10"),
        "+1": Decimal("0.05"),
    }
    _DEFAULT_RATE = Decimal("0.50")

    def __post_init__(self):
        if not self._PATTERN.match(self.code):
            raise InvalidCountryCodeError(
                f"Invalid country code: '{self.code}'. "
                f"Expected format: + followed by digits (e.g., +86)."
            )

    def base_rate(self) -> Money:
        """Return the base per-minute rate for this country."""
        amount = self._BASE_RATES.get(self.code, self._DEFAULT_RATE)
        return Money(amount, CNY)

    @classmethod
    def from_phone_number(cls, phone: str) -> "CountryCode":
        """Extract country code from a phone number.

        Tries known codes by descending length first, then falls back
        to regex extraction for unknown codes (so they get the default rate).
        """
        if not phone.startswith("+"):
            raise InvalidCountryCodeError(
                f"Phone number must start with '+': '{phone}'"
            )
        for code in sorted(cls._BASE_RATES, key=len, reverse=True):
            if phone.startswith(code):
                return cls(code)
        match = re.match(r"^\+(\d{1,3})", phone)
        if match:
            return cls(f"+{match.group(1)}")
        raise InvalidCountryCodeError(
            f"Cannot extract country code from: '{phone}'"
        )
