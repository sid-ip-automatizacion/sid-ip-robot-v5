"""
Core module for SID-IP Robot.

This module initializes the core components and exports key classes and functions
for AP API handling, SCCD API handling, and Nexus remote access.
"""

from .ap_management import get_controller
from .ruckus_api_handler.ruckus_sz_get_domains import get_domains
from .meraki_api_handler.meraki_get_org import get_org
from .meraki_api_handler.meraki_sw import get_switches as get_meraki_switches

from .sccd_api_handler.sccd_wo_connector import SCCD_WO
from .sccd_api_handler.sccd_ci_configurator import SCCD_CI_Configurator as SCCD_CI_CONF
from .sccd_api_handler.sccd_loc_connector import SCCD_LOC
from .sccd_api_handler.sccd_sr_connector import SCCD_SR

from .remote_access_handler import execute as nexus_remote_access


__all__ = ["get_controller", "get_domains", "get_org", "get_meraki_switches", 
           "SCCD_WO", "SCCD_CI_CONF", "SCCD_LOC", "SCCD_SR",
           "nexus_remote_access"]
