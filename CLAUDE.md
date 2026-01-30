# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SID-IP Robot is a Python desktop application for network operations and SCCD service desk tasks. It provides a Tkinter-based GUI for managing Access Points (Meraki, Fortinet, Ruckus) and SCCD work orders.

## Running the Application

```bash
python SIDIP_robot.py
```

The application requires authentication. Configure credentials via the "My account" menu after first login.

## Dependencies

Install required packages (not in requirements.txt):
- requests, python-dotenv, keyring, passlib, openpyxl, meraki, jinja2, beautifulsoup4

## Architecture

### Entry Point Flow
`SIDIP_robot.py` → `initialize.py` (AuthenticatedUser) → `gui/main_window.py` (UserEnvironment)

### Core Module (`core/`)
- **ap_management.py**: Factory pattern (`ControllerFactory`) creates vendor-specific AP controllers (MerakiController, FortiController, RuckusController) via `get_controller(controller_info)` function
- **meraki/**, **fortinet/**, **ruckus/**: Vendor-specific API implementations
- **sccd/**: Service desk connectors - SCCD_WO (work orders), SCCD_CI_CONF (configuration items), SCCD_LOC (locations), SCCD_SR (service requests)

### GUI Module (`gui/`)
- **main_window.py**: `UserEnvironment` class manages the main window with a scrollable work area. Modules load into `get_work_area()` frame
- **components/env_handler.py**: `EnvHandler` manages credentials (SCCD, Meraki) using OS keyring and .env file
- **sccd_mgmt/**: SCCD management UI modules (work order manager, back office, asset assignment)

### Adding New GUI Modules
Modules must follow this pattern:
```python
def main_function(root_win, ...other_args):
    # root_win is the Tkinter frame from UserEnvironment.get_work_area()
    # Build UI using root_win as master
```

## Environment Variables

Stored in `.env`:
- `SECRET_KEY_HASH`: Application password hash (pbkdf2_sha256)
- `LOGIN_USER_SCCD`, `OWNER_SCCD`: SCCD user configuration
- `LOGIN_USER_MERAKI`: Meraki user for keyring lookup

Credentials stored in OS keyring:
- `SCCD_KEY`: SCCD password
- `MERAKI_API_KEY`: Meraki API key

## UI Theming

Uses Azure dark theme (`resources/azure.tcl`):
```python
root.tk.call("source", "resources/azure.tcl")
root.tk.call("set_theme", "dark")
```

## Key Patterns

- Controller instances created via factory: `get_controller({"vendor": "meraki", ...})`
- SCCD connector validates credentials on init via `validate_credentials.status_code`
- Child windows use `tkinter.Toplevel()` to avoid blocking main window
