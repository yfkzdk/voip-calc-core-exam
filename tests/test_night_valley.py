"""Tests for NightValleyDiscount value object."""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from voip_calc_core.domain.night_valley import NightValleyDiscount
from voip_calc_core.domain.money import Money, CNY

CST = timezone(timedelta(hours=8))  # China Standard Time (Asia/Shanghai)


class TestNightValleyDefaults:
    def test_default_start_hour(self):
        nv = NightValleyDiscount()
        assert nv.start_hour == 23

    def test_default_end_hour(self):
        nv = NightValleyDiscount()
        assert nv.end_hour == 5

    def test_default_reduction(self):
        nv = NightValleyDiscount()
        assert nv.reduction == Decimal("0.02")

    def test_default_charging_timezone(self):
        nv = NightValleyDiscount()
        assert nv.charging_timezone == CST


class TestNightValleyValidation:
    def test_start_hour_out_of_range(self):
        with pytest.raises(ValueError):
            NightValleyDiscount(start_hour=24, end_hour=5)

    def test_end_hour_out_of_range(self):
        with pytest.raises(ValueError):
            NightValleyDiscount(start_hour=23, end_hour=-1)

    def test_negative_reduction(self):
        with pytest.raises(ValueError):
            NightValleyDiscount(reduction=Decimal("-0.01"))


class TestNightValleyIsApplicable:
    def test_during_night_valley_returns_true(self):
        nv = NightValleyDiscount()
        call_time = datetime(2026, 6, 6, 2, 0, 0, tzinfo=CST)
        assert nv.is_applicable(call_time) is True

    def test_before_night_valley_returns_false(self):
        nv = NightValleyDiscount()
        call_time = datetime(2026, 6, 5, 22, 0, 0, tzinfo=CST)
        assert nv.is_applicable(call_time) is False

    def test_at_start_boundary_returns_true(self):
        nv = NightValleyDiscount()
        call_time = datetime(2026, 6, 5, 23, 0, 0, tzinfo=CST)
        assert nv.is_applicable(call_time) is True

    def test_at_end_boundary_returns_false(self):
        nv = NightValleyDiscount()
        call_time = datetime(2026, 6, 5, 5, 0, 0, tzinfo=CST)
        assert nv.is_applicable(call_time) is False

    def test_same_day_range(self):
        nv = NightValleyDiscount(start_hour=22, end_hour=23)
        call_time = datetime(2026, 6, 5, 22, 30, 0, tzinfo=CST)
        assert nv.is_applicable(call_time) is True

    def test_custom_cross_midnight_range(self):
        nv = NightValleyDiscount(start_hour=22, end_hour=6)
        assert nv.is_applicable(datetime(2026, 6, 6, 1, 0, 0, tzinfo=CST)) is True
        assert nv.is_applicable(datetime(2026, 6, 5, 21, 0, 0, tzinfo=CST)) is False


class TestNightValleyTimezoneNormalization:
    """The charging timezone normalisation must be deterministic regardless
    of the timezone the caller passes in."""

    def test_utc_input_normalized_to_cst(self):
        nv = NightValleyDiscount()
        # UTC 18:00 = CST 02:00 (next day) — inside 23:00-05:00 night valley
        utc_time = datetime(2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc)
        assert nv.is_applicable(utc_time) is True

    def test_cst_input_stays_cst(self):
        nv = NightValleyDiscount()
        cst_time = datetime(2026, 6, 6, 2, 0, 0, tzinfo=CST)
        assert nv.is_applicable(cst_time) is True

    def test_custom_timezone_preserves_determinism(self):
        """With charging_timezone=UTC, the same UTC call_time should NOT be
        in the night valley (because UTC 18:00 ≠ 23:00-05:00)."""
        nv = NightValleyDiscount(charging_timezone=timezone.utc)
        utc_time = datetime(2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc)
        assert nv.is_applicable(utc_time) is False


class TestNightValleyReductionAmount:
    def test_returns_money_in_cny(self):
        nv = NightValleyDiscount()
        result = nv.reduction_amount()
        assert result == Money(Decimal("0.02"), CNY)


class TestNightValleyImmutability:
    def test_frozen_dataclass(self):
        nv = NightValleyDiscount()
        with pytest.raises(Exception):
            nv.start_hour = 22
