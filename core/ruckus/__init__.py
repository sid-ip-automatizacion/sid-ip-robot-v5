"""
Ruckus SmartZone integration module for SID-IP Robot.

This module provides classes and functions for interacting with the Ruckus SmartZone
controller API to manage Access Points.

Exports:
    - SmartZoneAPI: API client class for SmartZone controller
    - get_domains: Retrieve all domains from the SmartZone controller
"""

from .ruckus_sz_controller import SmartZoneAPI
from .ruckus_sz_get_domains import get_domains

__all__ = ["SmartZoneAPI", "get_domains"]
