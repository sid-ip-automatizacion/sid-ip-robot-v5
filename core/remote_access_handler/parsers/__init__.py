"""Vendor parser registry.

Each vendor name maps to a :class:`BaseParser` subclass.  Call
:func:`get_parser` to obtain an instance for a given vendor.
"""

from .fortinet import FortinetParser
from .cisco import CiscoParser
from .juniper import JuniperParser
from ..exceptions import UnsupportedVendorError

_PARSER_REGISTRY: dict[str, type] = {
    "fortinet": FortinetParser,
    "cisco": CiscoParser,
    "juniper": JuniperParser,
}


def get_parser(vendor: str):
    """Return a new parser instance for *vendor*."""
    cls = _PARSER_REGISTRY.get(vendor.lower())
    if cls is None:
        raise UnsupportedVendorError(f"No parser registered for vendor: {vendor}")
    return cls()


def register_parser(vendor: str, parser_cls: type) -> None:
    """Register a new or replacement parser for *vendor*."""
    _PARSER_REGISTRY[vendor.lower()] = parser_cls
