"""
Ruckus SmartZone Domain Retrieval Module.

This module provides a convenience function to retrieve all domains
from a Ruckus SmartZone controller.
"""

from .ruckus_sz_controller import SmartZoneAPI


def get_domains(controller_ip: str, username: str, password: str) -> list:
    """
    Retrieve all domains from a Ruckus SmartZone controller.

    Args:
        controller_ip: IP address or hostname of the SmartZone controller
        username: Login username
        password: Login password

    Returns:
        list: List of tuples (domain_name, domain_id)
    """
    api = SmartZoneAPI(controller_ip, username, password)
    return api.get_domains()
