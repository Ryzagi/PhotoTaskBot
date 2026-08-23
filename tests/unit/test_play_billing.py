"""Google Play billing: product catalog + unknown-product guard."""

from __future__ import annotations

from bot.services.play_billing import PRODUCT_CREDITS, PlayBillingService


def test_product_catalog():
    assert set(PRODUCT_CREDITS) == {"bamboo_20", "bamboo_50", "bamboo_100"}
    assert all(v > 0 for v in PRODUCT_CREDITS.values())


def test_not_configured_without_service_account():
    svc = PlayBillingService(db=None, billing=None, package_name="", sa_info=None)
    assert svc.configured is False
