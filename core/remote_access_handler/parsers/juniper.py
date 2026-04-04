"""Parser for Juniper devices (SRX and EX series)."""

import re

from .base import BaseParser
from .utils import (
    classify_interface_role,
    extract_cid,
    extract_device_from_hostname,
    extract_vlan_juniper,
    parse_interface_description_line,
)

_CMD_HOSTNAME = "show configuration system host-name | display set"
_CMD_CHASSIS = "show chassis hardware | match Chassis"
_CMD_VERSION = "show version | match Junos:"
_CMD_INTF_DESC = "show interfaces descriptions"


class JuniperParser(BaseParser):
    """Handles Juniper SRX (RT) and EX (SW) devices."""

    # -- Phase 1 -----------------------------------------------------------

    def initial_commands(self) -> list[str]:
        return [_CMD_HOSTNAME, _CMD_CHASSIS, _CMD_VERSION]

    def parse_initial(self, outputs: dict[str, str]) -> dict:
        info: dict = {"vendor": "juniper"}

        # Hostname
        for line in outputs[_CMD_HOSTNAME].splitlines():
            m = re.search(r"set system host-name\s+(\S+)", line)
            if m:
                info["hostname"] = m.group(1)
                break

        # Serial & Model
        for line in outputs[_CMD_CHASSIS].splitlines():
            m = re.match(r"Chassis\s+(\S+)\s+(\S+)", line.strip())
            if m:
                info["sn"] = m.group(1)
                info["model"] = m.group(2)
                break

        # Firmware
        for line in outputs[_CMD_VERSION].splitlines():
            m = re.search(r"Junos:\s+(\S+)", line)
            if m:
                info["firmware"] = m.group(1)
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
                        "vlan_mgmt": extract_vlan_juniper(interface),
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
            (
                d["interface"],
                f"show configuration interfaces {d['interface']}"
                " | display set | match address",
            )
            for d in interface_data["dcn"]
        ]

    def parse_dcn_detail(
        self, interface_name: str, output: str, interface_data: dict
    ) -> None:
        m = re.search(r"address\s+(\d+\.\d+\.\d+\.\d+)/", output)
        if m:
            for dcn in interface_data["dcn"]:
                if dcn["interface"] == interface_name:
                    dcn["ip_dcn"] = m.group(1)
                    break
