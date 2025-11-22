"""
Core module for SID-IP Robot.

This module initializes the core components and exports key classes and functions
for AP management and SCCD connectivity.
"""

from .ap_management import get_controller
from .sccd.sccd_wo_connector import SCCD as SCCD_WO
from .sccd.sccd_ci_configurator import SCCD_CI_Configurator as SCCD_CI_CONF
from .sccd.sccd_loc_connector import SCCD_LOC
from .sccd.sccd_sr_connector import SCCD_SR

__all__ = ["get_controller", "SCCD_WO", "SCCD_CI_CONF", "SCCD_LOC", "SCCD_SR"]
