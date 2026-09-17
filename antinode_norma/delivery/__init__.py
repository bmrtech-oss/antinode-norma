"""Delivery package for Norma BDD platform."""

from antinode_norma.delivery.testrail import TestRailDeliveryAdapter, DeliveryReport
from antinode_norma.delivery.xray import XrayDeliveryAdapter, XrayDeliveryReport

__all__ = [
    "TestRailDeliveryAdapter",
    "DeliveryReport",
    "XrayDeliveryAdapter",
    "XrayDeliveryReport",
]
