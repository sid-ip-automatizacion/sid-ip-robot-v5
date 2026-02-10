# SID-IP Robot

Task automation robot for the SID-IP team at Liberty Networks.

## Description

Desktop application developed in Python with Tkinter that provides tools for:

- **SCCD WO Management**: Work Order management in the Service Desk (SCCD)
- **AP Management**: Access Point configuration (Meraki, Fortinet, Ruckus)
- **Meraki SW ATP**: Meraki switch management with ATP
- **SCCD Multi-Asset Assignment**: Multiple asset assignment in SCCD
- **Back Office Management**: Back office management tools

## Requirements

- Python 3.8+
- Windows (for system keyring integration)

## Installation

```bash
pip install requests python-dotenv keyring passlib openpyxl meraki jinja2 beautifulsoup4
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
│   ├── meraki/             # Meraki integration
│   ├── fortinet/           # Fortinet integration
│   ├── ruckus/             # Ruckus SmartZone integration
│   └── sccd/               # SCCD connectors (WO, CI, LOC, SR)
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

## Development Team

Developed by the SID-IP team at Liberty Networks:
- Alvaro Molano
- Cesar Castillo
- Nicole Paz
- William Galindo
- Luis Solís

## Version

v5.4.6
