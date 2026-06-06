"""Tests for CustomerTier value object."""

import pytest
from decimal import Decimal

from voip_calc_core.domain.customer_tier import CustomerTier, TierEnum


class TestCustomerTier:
    def test_vip_discount_rate(self):
        tier = CustomerTier(TierEnum.VIP)
        assert tier.discount_rate() == Decimal("0.9")

    def test_normal_discount_rate(self):
        tier = CustomerTier(TierEnum.NORMAL)
        assert tier.discount_rate() == Decimal("1.0")

    def test_vip_label(self):
        assert CustomerTier(TierEnum.VIP).label() == "VIP"

    def test_normal_label(self):
        assert CustomerTier(TierEnum.NORMAL).label() == "NORMAL"

    def test_from_label_vip_case_insensitive(self):
        tier = CustomerTier.from_label("vip")
        assert tier.tier == TierEnum.VIP

    def test_from_label_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown customer tier"):
            CustomerTier.from_label("PLATINUM")

    def test_frozen_dataclass(self):
        tier = CustomerTier(TierEnum.VIP)
        with pytest.raises(Exception):
            tier.tier = TierEnum.NORMAL
