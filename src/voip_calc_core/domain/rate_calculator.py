"""RateCalculator — stateless domain service for per-minute rate calculation."""

from decimal import Decimal
from typing import Optional

from .call_context import CallContext
from .country_code import CountryCode
from .money import Money, CNY
from .night_valley import NightValleyDiscount


class RateCalculator:
    """Stateless domain service: base rate -> tier discount -> night reduction -> floor at Y=0.

    Usage::

        calculator = RateCalculator()
        rate = calculator.calculateRate(context)
    """

    def __init__(self, night_valley: Optional[NightValleyDiscount] = None):
        self._night_valley = night_valley or NightValleyDiscount()

    def calculateRate(self, context: CallContext) -> Money:
        """Return the final per-minute rate for *context*.

        Pipeline:
        1. Base rate by destination country code (from callee)
        2. Customer tier discount (VIP 0.9, NORMAL 1.0)
        3. Night valley reduction (-Y=0.02 if applicable, floor at Y=0.00)
        """
        country = CountryCode.from_phone_number(context.callee)
        base_rate = country.base_rate()

        discounted = base_rate * context.tier.discount_rate()

        if self._night_valley.is_applicable(context.call_time):
            result = discounted - self._night_valley.reduction_amount()
        else:
            result = discounted

        return result.at_least(Money(Decimal("0"), CNY))
