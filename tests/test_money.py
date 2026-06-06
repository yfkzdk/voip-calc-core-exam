"""Tests for Money value object."""

import pytest
from decimal import Decimal

from voip_calc_core.domain.money import Money, CNY, MoneyCurrencyMismatchError


class TestMoneyCreation:
    def test_create_with_decimal(self):
        m = Money(Decimal("10.50"), CNY)
        assert m.amount == Decimal("10.50")
        assert m.currency == CNY

    def test_create_with_int_coerces_to_decimal(self):
        m = Money(10, CNY)
        assert m.amount == Decimal("10")

    def test_create_with_float_coerces_via_str(self):
        m = Money(0.1, CNY)
        assert m.amount == Decimal("0.1")


class TestMoneyImmutability:
    def test_frozen_dataclass(self):
        m = Money(Decimal("5"), CNY)
        with pytest.raises(Exception):
            m.amount = Decimal("10")


class TestMoneyArithmetic:
    def test_add_same_currency(self):
        a = Money(Decimal("1.00"), CNY)
        b = Money(Decimal("2.00"), CNY)
        result = a + b
        assert result == Money(Decimal("3.00"), CNY)
        assert result is not a
        assert result is not b

    def test_add_currency_mismatch_raises(self):
        a = Money(Decimal("1"), CNY)
        b = Money(Decimal("1"), "USD")
        with pytest.raises(MoneyCurrencyMismatchError):
            a + b

    def test_mul_decimal(self):
        m = Money(Decimal("1.00"), CNY)
        result = m * Decimal("0.9")
        assert result == Money(Decimal("0.90"), CNY)

    def test_mul_float_safe(self):
        m = Money(Decimal("0.05"), CNY)
        result = m * 0.9
        assert result == Money(Decimal("0.045"), CNY)

    def test_mul_returns_new_instance(self):
        m = Money(Decimal("1"), CNY)
        result = m * 2
        assert result is not m


class TestMoneyAtLeast:
    def test_at_least_returns_self_when_larger(self):
        m = Money(Decimal("5.00"), CNY)
        assert m.at_least(Money(Decimal("3.00"), CNY)) is m

    def test_at_least_returns_floor_when_smaller(self):
        m = Money(Decimal("1.00"), CNY)
        result = m.at_least(Money(Decimal("2.00"), CNY))
        assert result == Money(Decimal("2.00"), CNY)

    def test_at_least_currency_mismatch_raises(self):
        m = Money(Decimal("1"), CNY)
        with pytest.raises(MoneyCurrencyMismatchError):
            m.at_least(Money(Decimal("1"), "USD"))
