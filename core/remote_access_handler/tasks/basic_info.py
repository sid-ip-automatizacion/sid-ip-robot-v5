"""``basic_info`` task – collects CID, hostname, channels, DCN, related
CIDs, serial number, device type, vendor, model, and firmware from a
network device.
"""

from .base import BaseTask
from .registry import register_task
from ..parsers import get_parser
from ..plugins.base import BaseConnectionPlugin


@register_task("basic_info")
class BasicInfoTask(BaseTask):
    """Gather basic inventory information from a single device.

    The task delegates command selection and output parsing to the
    vendor-specific :class:`~network_inventory.parsers.base.BaseParser`
    and uses the connection plugin only to send commands.

    Execution phases
    ----------------
    1. **Initial info** – hostname, model, serial, firmware, device type.
    2. **Interface analysis** – channels, DCN interfaces, related CIDs.
    3. **DCN detail** – IP address for each management interface
       (Cisco / Juniper need extra commands; Fortinet already has the IP).
    4. **Result assembly** – merge all phases into the output dict.
    """

    def execute(self, connection: BaseConnectionPlugin, vendor: str) -> dict:
        parser = get_parser(vendor)

        # Phase 1: initial device info
        raw_initial: dict[str, str] = {}
        for cmd in parser.initial_commands():
            raw_initial[cmd] = connection.send_command(cmd)
        initial_info = parser.parse_initial(raw_initial)

        # Phase 2: interface analysis
        setup_cmds = parser.interface_setup_commands(initial_info)
        if setup_cmds:
            connection.send_setup_commands(setup_cmds)

        raw_interfaces: dict[str, str] = {}
        for cmd in parser.interface_commands(initial_info):
            raw_interfaces[cmd] = connection.send_command(cmd)
        interface_data = parser.parse_interfaces(raw_interfaces, initial_info)

        # Phase 3: DCN detail (may be empty for vendors that already have IP)
        for intf_name, cmd in parser.dcn_detail_commands(interface_data):
            output = connection.send_command(cmd)
            parser.parse_dcn_detail(intf_name, output, interface_data)

        # Phase 4: assemble result
        return parser.build_result(initial_info, interface_data)
