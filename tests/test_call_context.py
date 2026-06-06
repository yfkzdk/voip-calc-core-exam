"""Tests for CallContext value object."""

import pytest
from datetime import datetime, timedelta, timezone

from voip_calc_core.domain.call_context import CallContext
from voip_calc_core.domain.customer_tier import CustomerTier, TierEnum

CST = timezone(timedelta(hours=8))  # China Standard Time


class TestCallContextCreation:
    def test_valid_context(self):
        ctx = CallContext(
            caller="+8613800000001",
            callee="+14150000000",
            call_time=datetime(2026, 6, 5, 14, 30, 0, tzinfo=CST),
            tier=CustomerTier(TierEnum.NORMAL),
        )
        assert ctx.caller == "+8613800000001"
        assert ctx.callee == "+14150000000"
        assert ctx.tier.tier == TierEnum.NORMAL

    def test_naive_datetime_raises(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            CallContext(
                caller="+8613800000001",
                callee="+14150000000",
                call_time=datetime(2026, 6, 5, 14, 30, 0),
                tier=CustomerTier(TierEnum.NORMAL),
            )


class TestCallContextImmutability:
    def test_frozen_dataclass(self):
        ctx = CallContext(
            caller="+8613800000001",
            callee="+14150000000",
            call_time=datetime(2026, 6, 5, 14, 30, 0, tzinfo=CST),
            tier=CustomerTier(TierEnum.NORMAL),
        )
        with pytest.raises(Exception):
            ctx.caller = "+8613900000000"
