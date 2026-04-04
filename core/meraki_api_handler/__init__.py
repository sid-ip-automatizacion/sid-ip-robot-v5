"""
Meraki integration module for SID-IP Robot.

This module provides classes and functions for interacting with the Meraki Dashboard API
to manage Access Points (APs) and Switches.

Exports:
    - get_org: Retrieve all organizations accessible with the API key
    - get_switches: Retrieve switch information from an organization
    - MerakiWLC: Wireless LAN Controller class for AP management
"""

from .meraki_sw import get_switches
from .meraki_get_org import get_org
from .meraki_ap import MerakiWLC

__all__ = ["get_org", "get_switches", "MerakiWLC"]

