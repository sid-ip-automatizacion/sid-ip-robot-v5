"""Abstract base class for vendor-specific parsers."""

from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Contract that every vendor parser must fulfil.

    The task layer calls the parser methods in a strict sequence:

    1. :meth:`initial_commands` / :meth:`parse_initial`
    2. :meth:`interface_setup_commands` / :meth:`interface_commands` /
       :meth:`parse_interfaces`
    3. :meth:`dcn_detail_commands` / :meth:`parse_dcn_detail`
    4. :meth:`build_result`
    """

    # ------------------------------------------------------------------
    # Phase 1 – initial device info
    # ------------------------------------------------------------------
    @abstractmethod
    def initial_commands(self) -> list[str]:
        """Return the list of commands needed to collect basic device info."""

    @abstractmethod
    def parse_initial(self, outputs: dict[str, str]) -> dict:
        """Parse the raw outputs into an *initial_info* dict.

        Required keys: ``hostname``, ``model``, ``sn``, ``firmware``,
        ``device``, ``vendor``.  Vendor-specific keys (e.g.
        ``multi_vdom``) are allowed and used in later phases.
        """

    # ------------------------------------------------------------------
    # Phase 2 – interface analysis
    # ------------------------------------------------------------------
    def interface_setup_commands(self, initial_info: dict) -> list[str]:
        """Return context-changing commands to run *before* interface commands.

        Default is an empty list (most vendors do not need this).
        """
        return []

    @abstractmethod
    def interface_commands(self, initial_info: dict) -> list[str]:
        """Return the commands that list interface descriptions / config."""

    @abstractmethod
    def parse_interfaces(self, outputs: dict[str, str], initial_info: dict) -> dict:
        """Parse interface outputs into an *interface_data* dict.

        Expected structure::

            {
                "cid": str | None,
                "channels": {cid: {"type": str, "ports": [str]}},
                "dcn": [{"interface": str, "ip_dcn": str|None, "vlan_mgmt": str|None}],
                "related": {cid: {"ports": [str]}},
            }
        """

    # ------------------------------------------------------------------
    # Phase 3 – DCN detail collection (optional per vendor)
    # ------------------------------------------------------------------
    def dcn_detail_commands(self, interface_data: dict) -> list[tuple[str, str]]:
        """Return ``(interface_name, command)`` pairs for DCN IP retrieval.

        Default is an empty list (vendors that already have the IP in the
        interface output, like Fortinet, do not need extra commands).
        """
        return []

    def parse_dcn_detail(
        self, interface_name: str, output: str, interface_data: dict
    ) -> None:
        """Update *interface_data* in-place with the parsed DCN IP."""

    # ------------------------------------------------------------------
    # Phase 4 – result assembly
    # ------------------------------------------------------------------
    def build_result(self, initial_info: dict, interface_data: dict) -> dict:
        """Assemble the final result dictionary.

        The default implementation works for all current vendors.
        Override only if a vendor needs special post-processing.
        """
        channels = tuple(
            {
                "channel_cid": cid,
                "channel_type": data["type"],
                "port": tuple(data["ports"]),
            }
            for cid, data in interface_data["channels"].items()
        )

        dcn = tuple(
            {"ip_dcn": d["ip_dcn"], "vlan_mgmt": d["vlan_mgmt"]}
            for d in interface_data["dcn"]
        )

        cids_related = tuple(
            {"cid_related": cid, "port": tuple(data["ports"])}
            for cid, data in interface_data["related"].items()
        )

        return {
            "cid": interface_data.get("cid"),
            "hostname": initial_info["hostname"],
            "channels": channels,
            "dcn": dcn,
            "cids_related": cids_related,
            "sn": initial_info["sn"],
            "device": initial_info["device"],
            "vendor": initial_info["vendor"],
            "model": initial_info["model"],
            "firmware": initial_info["firmware"],
        }
