"""Parser for Fortinet devices (FortiGate and FortiSwitch)."""

import re

from .base import BaseParser
from .utils import (
    CID_PATTERN,
    classify_interface_role,
    extract_cid,
    extract_device_from_hostname,
)

# Commands -----------------------------------------------------------------
_GET_STATUS = "get system status"
_SHOW_SYS_INTF = (
    "show system interface | grep 'edit\\|alias\\|interface\\|set ip\\|vlanid'"
)
_SHOW_PHYS_PORT = (
    "show switch physical-port | grep 'edit\\|alias\\|description'"
)


class FortinetParser(BaseParser):
    """Handles both FortiGate (RT) and FortiSwitch (SW) output."""

    # -- Phase 1 -----------------------------------------------------------

    def initial_commands(self) -> list[str]:
        return [_GET_STATUS]

    def parse_initial(self, outputs: dict[str, str]) -> dict:
        output = outputs[_GET_STATUS]
        info: dict = {"vendor": "fortinet"}

        for line in output.splitlines():
            line = line.strip()

            if line.startswith("Version:"):
                # "Version: FortiGate-60F v6.4.6,build6083,210729 (GA)"
                parts = line.split()
                info["model"] = parts[1]
                info["firmware"] = parts[2]

            elif line.startswith("Serial-Number:"):
                info["sn"] = line.split(":", 1)[1].strip()

            elif line.startswith("Hostname:"):
                info["hostname"] = line.split(":", 1)[1].strip()

            elif line.startswith("Virtual domain configuration:"):
                vdom_val = line.split(":", 1)[1].strip().lower()
                info["multi_vdom"] = vdom_val == "multiple"

        # Device type from hostname; fallback to model name.
        info["device"] = extract_device_from_hostname(info.get("hostname", ""))
        if info["device"] is None:
            model = info.get("model", "")
            if "FortiGate" in model:
                info["device"] = "rt"
            elif "FortiSwitch" in model:
                info["device"] = "sw"

        return info

    # -- Phase 2 -----------------------------------------------------------

    def interface_setup_commands(self, initial_info: dict) -> list[str]:
        if initial_info["device"] == "rt" and initial_info.get("multi_vdom"):
            return ["config vdom", "edit root"]
        return []

    def interface_commands(self, initial_info: dict) -> list[str]:
        commands = [_SHOW_SYS_INTF]
        if initial_info["device"] == "sw":
            commands.append(_SHOW_PHYS_PORT)
        return commands

    def parse_interfaces(self, outputs: dict[str, str], initial_info: dict) -> dict:
        sys_output = outputs[_SHOW_SYS_INTF]
        interfaces = _parse_interface_blocks(sys_output)

        result: dict = {
            "cid": None,
            "channels": {},
            "dcn": [],
            "related": {},
        }

        device = initial_info["device"]

        for intf in interfaces:
            name = intf["name"]
            alias = intf.get("alias")

            if not alias:
                continue

            cid = extract_cid(alias)
            if cid is None:
                continue

            role = classify_interface_role(name)

            if role == "dcn":
                if result["cid"] is None:
                    result["cid"] = cid
                result["dcn"].append(
                    {
                        "interface": name,
                        "ip_dcn": intf.get("ip"),
                        "vlan_mgmt": intf.get("vlanid"),
                    }
                )

            elif role in ("ip_transit", "mpls", "mpls_voice"):
                bucket = result["channels"].setdefault(
                    cid, {"type": role, "ports": []}
                )
                bucket["ports"].append(name)

            elif device == "rt":
                # Any Fortinet-RT interface with a CID alias that is
                # neither DCN nor channel is a related CID.
                bucket = result["related"].setdefault(cid, {"ports": []})
                bucket["ports"].append(name)

        # FortiSwitch: related CIDs come from physical port descriptions.
        if device == "sw" and _SHOW_PHYS_PORT in outputs:
            for item in _parse_physical_ports(outputs[_SHOW_PHYS_PORT]):
                bucket = result["related"].setdefault(
                    item["cid"], {"ports": []}
                )
                bucket["ports"].append(item["port"])

        return result

    # -- Fortinet already has IP/VLAN in sys-interface output --------------

    def dcn_detail_commands(self, interface_data: dict) -> list[tuple[str, str]]:
        return []

    def parse_dcn_detail(
        self, interface_name: str, output: str, interface_data: dict
    ) -> None:
        pass  # pragma: no cover


# ── Internal helpers ─────────────────────────────────────────────────────

_EDIT_QUOTED = re.compile(r'edit\s+"([^"]+)"')


def _parse_interface_blocks(output: str) -> list[dict]:
    """Parse the filtered ``show system interface`` output into blocks.

    Each block represents one interface with keys: ``name``, ``ip``,
    ``alias``, ``parent_interface``, ``vlanid``.
    """
    interfaces: list[dict] = []
    current: dict | None = None

    for line in output.splitlines():
        stripped = line.strip()

        m = _EDIT_QUOTED.match(stripped)
        if m:
            if current is not None:
                interfaces.append(current)
            current = {"name": m.group(1)}
            continue

        if current is None:
            continue

        if stripped.startswith("set ip "):
            parts = stripped.split()
            if len(parts) >= 3:
                current["ip"] = parts[2]

        elif stripped.startswith("set alias "):
            m_alias = re.search(r'"([^"]*)"', stripped)
            if m_alias:
                current["alias"] = m_alias.group(1)

        elif stripped.startswith("set interface "):
            m_intf = re.search(r'"([^"]*)"', stripped)
            if m_intf:
                current["parent_interface"] = m_intf.group(1)

        elif stripped.startswith("set vlanid "):
            current["vlanid"] = stripped.split()[-1]

    if current is not None:
        interfaces.append(current)

    return interfaces


def _parse_physical_ports(output: str) -> list[dict]:
    """Parse ``show switch physical-port`` for related CIDs.

    Returns a list of ``{"cid": ..., "port": ...}`` dicts.
    """
    related: list[dict] = []
    current_port: dict | None = None

    for line in output.splitlines():
        stripped = line.strip()

        m = _EDIT_QUOTED.match(stripped)
        if m:
            if current_port is not None:
                _maybe_add_related(current_port, related)
            current_port = {"name": m.group(1)}
            continue

        if current_port is None:
            continue

        if stripped.startswith("set description "):
            m_desc = re.search(r'"([^"]*)"', stripped)
            if m_desc:
                current_port["description"] = m_desc.group(1)

    if current_port is not None:
        _maybe_add_related(current_port, related)

    return related


def _maybe_add_related(port: dict, related: list[dict]) -> None:
    desc = port.get("description", "")
    if not desc:
        return
    cid = extract_cid(desc)
    if cid is not None:
        related.append({"cid": cid, "port": port["name"]})
