"""
Initialization module for the Fortinet core functionality.

This module exposes the FortigateAPI class for interacting with Fortinet devices.
"""
from .fortigate_wifi_controller import FortigateAPI

__all__ = ["FortigateAPI"]
