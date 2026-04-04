"""Shared regex patterns and classification helpers used by all vendor parsers."""

import re

# Matches CID patterns like: 663037.HN, 37667718.1.1.DO, 8016974.SV
CID_PATTERN = re.compile(r"\d+(?:\.\d+)*\.[A-Z]{2}")

# Interface description line pattern (Cisco / Juniper)
# Handles both "up/down" and "admin down" status fields.
INTF_DESC_LINE = re.compile(
    r"^(\S+)\s+"                     # Interface name
    r"(?:admin\s+)?(?:up|down)\s+"   # Status (with optional "admin" prefix)
    r"(?:up|down)"                   # Protocol / Link
    r"(?:\s+(.+?))?\s*$"            # Optional description
)


def classify_interface_role(text: str) -> str | None:
    """Classify a text (interface name or description) by its network role.

    Returns one of: ``"dcn"``, ``"ip_transit"``, ``"mpls_voice"``, ``"mpls"``,
    or ``None`` when no known pattern is found.
    """
    upper = text.upper()

    if re.search(r"(?:MGT|MGMT|GESTION)", upper):
        return "dcn"
    # Check voice before generic MPLS to avoid false positives.
    if re.search(r"(?:MPLS[_\-\s]?VOICE|VOICE|MYUC|VOIP)", upper):
        return "mpls_voice"
    if re.search(r"(?:IPT|INET)", upper):
        return "ip_transit"
    if re.search(r"MPLS", upper):
        return "mpls"
    return None


def extract_device_from_hostname(hostname: str) -> str | None:
    """Derive the device type (``"rt"`` or ``"sw"``) from the hostname prefix."""
    upper = hostname.upper()
    if upper.startswith("RT"):
        return "rt"
    if upper.startswith("SW"):
        return "sw"
    return None


def extract_cid(text: str) -> str | None:
    """Return the first CID found in *text*, or ``None``."""
    match = CID_PATTERN.search(text)
    return match.group(0) if match else None


def parse_interface_description_line(line: str) -> tuple[str | None, str]:
    """Parse a single line from ``show interface(s) description(s)``.

    Returns ``(interface_name, description)`` or ``(None, "")`` when the
    line does not match the expected format.
    """
    m = INTF_DESC_LINE.match(line.strip())
    if m:
        return m.group(1), (m.group(2) or "").strip()
    return None, ""


def extract_vlan_cisco(interface_name: str) -> str | None:
    """Extract the VLAN / unit number from a Cisco interface name.

    Handles ``Vl335``, ``Vlan335``, ``BDI141``, ``BD141``, ``Gi0/0.2001``.
    """
    m = re.match(r"(?:Vl(?:an)?)(\d+)", interface_name, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.match(r"BDI?(\d+)", interface_name, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\.(\d+)$", interface_name)
    if m:
        return m.group(1)
    return None


def extract_vlan_juniper(interface_name: str) -> str | None:
    """Extract the unit / VLAN number from a Juniper interface name.

    Handles ``ge-0/0/0.147``, ``irb.335``, ``vlan.100``.
    """
    m = re.search(r"\.(\d+)$", interface_name)
    return m.group(1) if m else None
