"""Connection plugin registry.

Maps each vendor name to the appropriate plugin class and device-type
parameter.  Call :func:`get_connection_plugin` to obtain a ready-to-use
(but not yet connected) plugin instance.
"""

from .netmiko_plugin import NetmikoPlugin
from .scrapli_plugin import ScrapliPlugin
from ..exceptions import UnsupportedVendorError

# (plugin_class, device_type_kwarg_or_None)
_VENDOR_PLUGIN_MAP: dict[str, tuple] = {
    "fortinet": (NetmikoPlugin, "fortinet"),
    "juniper": (NetmikoPlugin, "juniper_junos"),
    "cisco":   (ScrapliPlugin, None),
}


def get_connection_plugin(vendor: str, hostname: str, username: str, password: str):
    """Factory: return an *unconnected* plugin for the given vendor."""
    entry = _VENDOR_PLUGIN_MAP.get(vendor.lower())
    if entry is None:
        raise UnsupportedVendorError(f"No connection plugin for vendor: {vendor}")

    plugin_cls, device_type = entry
    if device_type is not None:
        return plugin_cls(hostname, username, password, device_type)
    return plugin_cls(hostname, username, password)


def register_plugin(vendor: str, plugin_cls, device_type: str | None = None) -> None:
    """Register a new or replacement connection plugin for a vendor."""
    _VENDOR_PLUGIN_MAP[vendor.lower()] = (plugin_cls, device_type)
