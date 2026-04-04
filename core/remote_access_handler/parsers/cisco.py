"""Parser for Cisco IOS / IOS XE devices (routers and switches)."""

import re

from .base import BaseParser
from .utils import (
    classify_interface_role,
    extract_cid,
    extract_device_from_hostname,
    extract_vlan_cisco,
    parse_interface_description_line,
)

_CMD_HOSTNAME = "show running-config | i hostname"
_CMD_INVENTORY = "show inventory | i SN"
_CMD_VERSION = "show version | i Version"
_CMD_INTF_DESC = "show interface description"


class CiscoParser(BaseParser):
    """Handles Cisco IOS and IOS XE devices (routers and switches)."""

    # -- Phase 1 -----------------------------------------------------------

    def initial_commands(self) -> list[str]:
        return [_CMD_HOSTNAME, _CMD_INVENTORY, _CMD_VERSION]

    def parse_initial(self, outputs: dict[str, str]) -> dict:
        info: dict = {"vendor": "cisco"}

        # Hostname
        for line in outputs[_CMD_HOSTNAME].splitlines():
            m = re.match(r"hostname\s+(\S+)", line.strip())
            if m:
                info["hostname"] = m.group(1)
                break

        # Model & Serial (first matching line)
        for line in outputs[_CMD_INVENTORY].splitlines():
            m = re.search(r"PID:\s*(\S+)\s*,.*SN:\s*(\S+)", line)
            if m:
                info["model"] = m.group(1)
                info["sn"] = m.group(2)
                break

        # Firmware (first line containing "Version")
        for line in outputs[_CMD_VERSION].splitlines():
            m = re.search(r"Version\s+([\d.()A-Za-z]+)", line)
            if m:
                info["firmware"] = m.group(1).rstrip(",")
                break

        info["device"] = extract_device_from_hostname(info.get("hostname", ""))
        return info

    # -- Phase 2 -----------------------------------------------------------

    def interface_commands(self, initial_info: dict) -> list[str]:
        return [_CMD_INTF_DESC]

    def parse_interfaces(self, outputs: dict[str, str], initial_info: dict) -> dict:
        output = outputs[_CMD_INTF_DESC]

        result: dict = {
            "cid": None,
            "channels": {},
            "dcn": [],
            "related": {},
        }

        for line in output.splitlines():
            interface, description = parse_interface_description_line(line)
            if interface is None or not description:
                continue

            cid = extract_cid(description)
            if cid is None:
                continue

            role = classify_interface_role(description)

            if role == "dcn":
                if result["cid"] is None:
                    result["cid"] = cid
                result["dcn"].append(
                    {
                        "interface": interface,
                        "ip_dcn": None,
                        "vlan_mgmt": extract_vlan_cisco(interface),
                    }
                )

            elif role in ("ip_transit", "mpls", "mpls_voice"):
                bucket = result["channels"].setdefault(
                    cid, {"type": role, "ports": []}
                )
                bucket["ports"].append(interface)

            else:
                bucket = result["related"].setdefault(cid, {"ports": []})
                bucket["ports"].append(interface)

        return result

    # -- Phase 3 -----------------------------------------------------------

    def dcn_detail_commands(self, interface_data: dict) -> list[tuple[str, str]]:
        return [
            (d["interface"], f"show running interface {d['interface']}")
            for d in interface_data["dcn"]
        ]

    def parse_dcn_detail(
        self, interface_name: str, output: str, interface_data: dict
    ) -> None:
        m = re.search(r"ip\s+address\s+(\d+\.\d+\.\d+\.\d+)", output)
        if m:
            for dcn in interface_data["dcn"]:
                if dcn["interface"] == interface_name:
                    dcn["ip_dcn"] = m.group(1)
                    break
