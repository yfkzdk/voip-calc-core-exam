"""Tests for CountryCode value object."""

import pytest
from decimal import Decimal

from voip_calc_core.domain.country_code import CountryCode, InvalidCountryCodeError
from voip_calc_core.domain.money import Money, CNY


class TestCountryCodeCreation:
    def test_valid_code(self):
        cc = CountryCode("+86")
        assert cc.code == "+86"

    def test_code_without_plus_raises(self):
        with pytest.raises(InvalidCountryCodeError):
            CountryCode("86")

    def test_code_with_letters_raises(self):
        with pytest.raises(InvalidCountryCodeError):
            CountryCode("+AB")

    def test_empty_code_raises(self):
        with pytest.raises(InvalidCountryCodeError):
            CountryCode("")


class TestCountryCodeBaseRate:
    def test_china_rate(self):
        assert CountryCode("+86").base_rate() == Money(Decimal("0.10"), CNY)

    def test_us_rate(self):
        assert CountryCode("+1").base_rate() == Money(Decimal("0.05"), CNY)

    def test_unknown_country_default_rate(self):
        assert CountryCode("+44").base_rate() == Money(Decimal("0.50"), CNY)


class TestCountryCodeFromPhoneNumber:
    def test_china_phone(self):
        cc = CountryCode.from_phone_number("+8613800000001")
        assert cc.code == "+86"

    def test_us_phone(self):
        cc = CountryCode.from_phone_number("+14150000000")
        assert cc.code == "+1"

    def test_unknown_phone_extracts_prefix(self):
        cc = CountryCode.from_phone_number("+4420000000000")
        assert cc.code == "+44"

    def test_phone_without_plus_raises(self):
        with pytest.raises(InvalidCountryCodeError):
            CountryCode.from_phone_number("8613800000001")

    def test_phone_too_short_raises(self):
        with pytest.raises(InvalidCountryCodeError):
            CountryCode.from_phone_number("+")


class TestCountryCodeImmutability:
    def test_frozen_dataclass(self):
        cc = CountryCode("+86")
        with pytest.raises(Exception):
            cc.code = "+1"
