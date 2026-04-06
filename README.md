# SID-IP Robot

Task automation robot for the SID-IP team at Liberty Networks.

## Development Team

Developed by the SID-IP team at Liberty Networks:
- Alvaro Molano
- Cesar Castillo
- Nicole Paz
- William Galindo
- Luis Solís
- Edward Antolinez
- Jeison Agudelo 
- Ennio Gamboa

## Version

v5.5.1

## Description

Desktop application developed in Python with Tkinter that provides tools for:

- **SCCD WO Management**: Work Order management in the Service Desk (SCCD)
- **AP Management**: Access Point configuration (Meraki, Fortinet, Ruckus) and SCCD integration
- **Meraki SW ATP**: Meraki switch management with ATP
- **SCCD Multi-Asset Assignment**: Multiple asset assignment in SCCD
- **Nexus Management**: Network orchestration and SCCD integration
- **Back Office Management**: Back office management tools


## Requirements

- Python 3.8+
- Windows (for system keyring integration)

## Installation

```bash
pip install requests python-dotenv keyring passlib openpyxl meraki jinja2 beautifulsoup4 nornir nornir-utils netmiko scrapli[ssh2] ssh2-python
pip install -r requierements.txt
```
or 
```bash
pip install -r requierements.txt
```

## Running

```bash
python SIDIP_robot.py
```

On first launch, configure credentials from the **My account** menu:
- **Configure SCCD**: SCCD username and password
- **Configure Meraki API Key**: Meraki API key

## Project Structure

```
├── SIDIP_robot.py      # Main entry point
├── initialize.py       # User authentication
├── core/               # Business logic and APIs
│   ├── ap_management.py    # AP controller factory
│   ├── meraki_api_handler/             # Meraki integration
│   ├── fortinet_api_handler/           # Fortinet integration
│   ├── ruckus_api_handler/             # Ruckus SmartZone integration
│   ├── sccd_api_handler/               # SCCD connectors (WO, CI, LOC, SR)
│   └── remote_access_handler           # ssh access connector
├── gui/                # Graphical interface
│   ├── main_window.py      # UserEnvironment (main window)
│   ├── components/         # Reusable components
│   └── sccd_mgmt/          # SCCD management modules
├── utils/              # Helper utilities
├── config/             # Configuration
├── resources/          # Icons and themes (azure.tcl)
├── outputs/            # Output files
└── tests/              # Tests
```

## Configuration

The application uses:
- **`.env` file**: Environment variables (users, password hash)
- **System keyring**: Secure storage for passwords and API keys

Variables in `.env`:
- `SECRET_KEY_HASH`: Application access password hash
- `LOGIN_USER_SCCD`: SCCD login user
- `OWNER_SCCD`: Owner person in SCCD
- `LOGIN_USER_MERAKI`: User for Meraki API key lookup
- `LOGIN_USER_RADIUS`: Radius user for ssh access
- `LOGIN_USER_TEMPORAL`: Temporal user for ssh access

## Module Development

### Requirements for integrating modules with UserEnvironment

Modules to integrate must:
1. Be written in Python with Tkinter GUI
2. Have an initial function that accepts `root_win` as the first argument
3. Use `root_win` as the main container (it's a Tkinter Frame)

### Module Example

```python
# my_module.py
import tkinter
from tkinter import ttk

def main_function(root_win, username, password, url=None):
    """
    Module initial function.

    Args:
        root_win: Tkinter Frame provided by UserEnvironment
        username: Username for the functionality
        password: Password
        url: Optional URL
    """
    title = ttk.Label(master=root_win, text="My Module")
    title.pack(pady=10)

    content_frame = ttk.Frame(master=root_win)
    content_frame.pack(fill="both", expand=True)

    # ... rest of implementation
```


# remote_access_handler

A Python package for parallel collection of structured information from network devices (Cisco, Fortinet, Juniper) via SSH, orchestrated by [Nornir](https://nornir.readthedocs.io/).

## Architecture

```
network_inventory/
├── __init__.py              # Public API: execute()
├── orchestrator.py          # Nornir setup, parallel execution, result aggregation
├── inventory.py             # (built into orchestrator) Dict-based Nornir inventory
├── exceptions.py            # Custom exception hierarchy
│
├── tasks/                   # Task layer (what to do)
│   ├── registry.py          # @register_task decorator + TaskRegistry
│   ├── base.py              # BaseTask ABC
│   └── basic_info.py        # "basic_info" task implementation
│
├── plugins/                 # Connection layer (how to talk to devices)
│   ├── __init__.py          # get_connection_plugin() factory + registry
│   ├── base.py              # BaseConnectionPlugin ABC
│   ├── netmiko_plugin.py    # Netmiko (Fortinet, Juniper)
│   └── scrapli_plugin.py    # Scrapli IOSXEDriver (Cisco)
│
└── parsers/                 # Parsing layer (how to interpret output)
    ├── __init__.py          # get_parser() factory + registry
    ├── base.py              # BaseParser ABC
    ├── utils.py             # Shared regex, CID detection, classification helpers
    ├── fortinet.py          # FortiGate / FortiSwitch parser
    ├── cisco.py             # Cisco IOS / IOS XE parser
    └── juniper.py           # Juniper SRX / EX parser
```

### Layer responsibilities

| Layer | Knows about | Does NOT know about |
|---|---|---|
| **Orchestrator** | Nornir, task names, device list | Vendor details, SSH, parsing |
| **Tasks** | Execution phases, parser + plugin APIs | SSH internals, regex, vendor quirks |
| **Plugins** | SSH libraries (netmiko / scrapli) | What commands mean, how to parse |
| **Parsers** | Vendor CLI output formats, regex | How connections are established |

## Installation

```bash
pip install nornir nornir-utils netmiko scrapli
```

> The package itself is used as a local import — no `setup.py` is required unless you want to distribute it.

## Quick start

```python
from network_inventory import execute

results = execute({
    "username": "admin",
    "password": "s3cret",
    "task": "basic_info",
    "devices": (
        ("10.0.0.1", "cisco"),
        ("10.0.0.2", "fortinet"),
        ("10.0.0.3", "juniper"),
    ),
})

for r in results:
    if r.get("failed"):
        print(f"FAILED {r['host']}: {r['error']}")
    else:
        print(f"{r['hostname']} — CID {r['cid']}")
```

### Input format

```python
{
    "username": str,
    "password": str,
    "task": str,           # registered task name, e.g. "basic_info"
    "devices": (
        (ip: str, vendor: str),  # vendor: "cisco" | "fortinet" | "juniper"
        ...
    ),
}
```

### Output format (`basic_info`)

One dict per device:

```python
{
    "cid": "00000.ZZ",
    "hostname": "RT_UTTEE_JOSE-MERENGUE-AVE17_MAIN_00000.ZZ",
    "channels": (
        {"channel_cid": "XXXXX.SV", "channel_type": "ip_transit", "port": ("BD106",)},
        {"channel_cid": "YYYYY.SV", "channel_type": "mpls", "port": ("BD617",)},
    ),
    "dcn": (
        {"ip_dcn": "10.10.10.65", "vlan_mgmt": "141"},
    ),
    "cids_related": (),
    "sn": "CAT2018V04X",
    "device": "rt",
    "vendor": "cisco",
    "model": "ASR-920-24SZ-IM",
    "firmware": "17.03.06",
}
```

Failed devices return:

```python
{"host": "10.0.0.99", "failed": True, "error": "Connection timed out"}
```

---

## How to add a new task

### 1. Create the task file

```
network_inventory/tasks/my_task.py
```

### 2. Implement the task class

```python
from .base import BaseTask
from .registry import register_task
from ..parsers import get_parser
from ..plugins.base import BaseConnectionPlugin


@register_task("my_task")
class MyTask(BaseTask):
    def execute(self, connection: BaseConnectionPlugin, vendor: str) -> dict:
        parser = get_parser(vendor)

        # Use connection.send_command() to collect raw output
        output = connection.send_command("show version")

        # Use parser methods or write new parser methods
        # ... process output ...

        return {"key": "value"}
```

### 3. Register the import

Add this line to `remote_access_handler/tasks/__init__.py`:

```python
from . import my_task  # noqa: F401
```

### 4. Extend parsers if needed

If the new task needs to parse new command output, add methods to `BaseParser` (abstract or with default implementations) and implement them in each vendor parser. See [Extending a parser](#extending-a-parser-with-new-methods) below.

### 5. Call it

```python
execute({"username": "u", "password": "p", "task": "my_task", "devices": (...)})
```

---

## How to add a new vendor

### 1. Create the parser

```
network_inventory/parsers/newvendor.py
```

Subclass `BaseParser` and implement all abstract methods:

```python
from .base import BaseParser


class NewVendorParser(BaseParser):
    def initial_commands(self) -> list[str]:
        return ["show system info"]

    def parse_initial(self, outputs):
        # Extract hostname, model, sn, firmware, device, vendor
        ...

    def interface_commands(self, initial_info):
        return ["show interfaces"]

    def parse_interfaces(self, outputs, initial_info):
        # Return {"cid": ..., "channels": {}, "dcn": [], "related": {}}
        ...

    # Override dcn_detail_commands / parse_dcn_detail if needed
    # build_result() is inherited and usually does not need overriding
```

### 2. Register it

In `network_inventory/parsers/__init__.py`:

```python
from .newvendor import NewVendorParser

_PARSER_REGISTRY["newvendor"] = NewVendorParser
```

### 3. Create or reuse a connection plugin

If the new vendor uses Netmiko, just register a mapping:

```python
# In network_inventory/plugins/__init__.py
_VENDOR_PLUGIN_MAP["newvendor"] = (NetmikoPlugin, "newvendor_os")
```

If it needs a completely new transport (e.g. REST API), subclass `BaseConnectionPlugin`:

```python
# network_inventory/plugins/rest_plugin.py
from .base import BaseConnectionPlugin


class RestPlugin(BaseConnectionPlugin):
    def connect(self):
        # Establish API session
        ...

    def send_command(self, command: str) -> str:
        # Translate command to API call, return text output
        ...

    def disconnect(self):
        ...
```

Then register:

```python
_VENDOR_PLUGIN_MAP["newvendor"] = (RestPlugin, None)
```

---

## How to add a new channel type

Channel types are classified in `parsers/utils.py` → `classify_interface_role()`.

### 1. Add the pattern

Edit the `classify_interface_role` function:

```python
def classify_interface_role(text: str) -> str | None:
    upper = text.upper()
    if re.search(r"(?:MGT|MGMT|GESTION)", upper):
        return "dcn"
    if re.search(r"(?:MPLS[_\-\s]?VOICE|VOICE|MYUC|VOIP)", upper):
        return "mpls_voice"
    if re.search(r"(?:IPT|INET)", upper):
        return "ip_transit"
    if re.search(r"MPLS", upper):
        return "mpls"
    # ← Add new channel types here, before the final return
    if re.search(r"NEW_PATTERN", upper):
        return "new_type"
    return None
```

> **Order matters:** more specific patterns (e.g. MPLS_VOICE) must come before generic ones (e.g. MPLS).

### 2. Allow it in the task

In each vendor parser's `parse_interfaces`, the channel-type check is:

```python
elif role in ("ip_transit", "mpls", "mpls_voice"):
```

Add the new type to this tuple:

```python
elif role in ("ip_transit", "mpls", "mpls_voice", "new_type"):
```

---

## Extending a parser with new methods

When a new task requires parsing output that existing parsers don't handle:

### 1. Add the method to `BaseParser`

```python
# parsers/base.py
class BaseParser(ABC):
    ...

    def parse_new_thing(self, output: str) -> dict:
        """Default implementation for backward compatibility."""
        raise NotImplementedError
```

Use a default implementation (or `raise NotImplementedError`) so that existing vendor parsers continue to work for existing tasks.

### 2. Implement in each vendor parser

```python
# parsers/cisco.py
class CiscoParser(BaseParser):
    ...

    def parse_new_thing(self, output: str) -> dict:
        # Cisco-specific parsing
        ...
```

### 3. Call from the new task

```python
parser = get_parser(vendor)
output = connection.send_command("show new thing")
data = parser.parse_new_thing(output)
```

---

## Modifying existing output fields

### Adding a new field to `basic_info` result

1. Collect the raw data in the appropriate parser phase (initial, interface, or DCN detail).
2. Store it in `initial_info` or `interface_data`.
3. Override `build_result` in the parser (or edit the base class if all vendors share it):

```python
def build_result(self, initial_info, interface_data):
    result = super().build_result(initial_info, interface_data)
    result["new_field"] = initial_info.get("new_field")
    return result
```

### Modifying an existing field

Find where the field is populated in the vendor parser (`parse_initial`, `parse_interfaces`, or `parse_dcn_detail`) and adjust the logic. The `build_result` method simply reads whatever was stored in earlier phases.

---

## Error handling

All custom exceptions inherit from `NetworkInventoryError`:

| Exception | When |
|---|---|
| `DeviceConnectionError` | SSH / transport connection failure |
| `CommandExecutionError` | A command sent to the device fails |
| `ParseError` | Raw output cannot be interpreted |
| `TaskNotFoundError` | Requested task name is not in the registry |
| `UnsupportedVendorError` | No parser or plugin for the vendor |

Failed devices do **not** abort the entire run — they appear in the results list with `"failed": True`.

---

## Connection plugin reference

| Vendor | Library | device_type / driver | Transport |
|---|---|---|---|
| Fortinet | Netmiko | `fortinet` | SSH |
| Juniper | Netmiko | `juniper_junos` | SSH |
| Cisco | Scrapli | `IOSXEDriver` | ssh2 |

---

## Fortinet-specific notes

- **FortiGate without VDOM:** standard command flow.
- **FortiGate with multi-VDOM:** the parser automatically detects `Virtual domain configuration: multiple` and sends `config vdom` → `edit root` before interface commands.
- **FortiSwitch:** classified as `device: "sw"`.  An extra command (`show switch physical-port`) is sent to discover related CIDs from physical port descriptions.
- For Fortinet, interface **names** determine the role (DCN / channel / related), and the **alias** contains the CID.
- For Cisco and Juniper, the interface **description** determines both the role and the CID.

