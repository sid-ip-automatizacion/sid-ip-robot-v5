"""
Meraki Wireless LAN Controller (WLC) Module.

This module receives the organization ID (org_id) and MERAKI API_KEY to retrieve
Access Point (AP) information from the organization.

The module returns the following information for each AP in the organization
as a list of dictionaries [{}, {}, ...]:

    - name: AP device name
    - model: AP model number
    - description: Device notes/description
    - site: Network name
    - mac: MAC address
    - ip: Local IP address
    - serial: Serial number
    - status: Connection status
    - current_clients: Number of connected wireless clients
    - address: Physical address

TODO: Fix getOrganizationDevicesStatuses (Deprecated API endpoint that may be
      removed in future Meraki Dashboard versions)
"""

import meraki
from time import sleep
from pprint import pprint


class MerakiWLC:
    """
    Meraki Wireless LAN Controller API client.

    Provides methods to retrieve and configure Access Points from Meraki Dashboard.

    Attributes:
        api_key (str): Meraki Dashboard API key
        org_id (str): Organization ID to query
        net (dict): Mapping of network ID to network name
        org_devices (list): List of all organization devices
        info_org_devices (list): Processed list of AP information
        serial_clients_map (dict): Mapping of AP serial to connected client count
    """

    def __init__(self, api_key: str, org_id: str):
        """
        Initialize the MerakiWLC client.

        Args:
            api_key: Meraki Dashboard API key
            org_id: Organization ID to manage
        """
        self.api_key = api_key
        self.org_id = org_id
        self.net = {}
        self.org_devices = []
        self.org_devices_for_loc_check = {}
        self.org_devices_for_addr_check = {}
        self.info_org_devices = []
        self.serial_clients_map = {}  # Mapping of serial to connected client count
        self.dashboard = meraki.DashboardAPI(api_key, output_log=False, print_console=False)

    def get(self) -> list:
        """
        Retrieve all Access Points from the organization.

        Fetches device statuses, device details, networks, and client counts
        to build a comprehensive list of AP information.

        Returns:
            list: List of dictionaries containing AP information, or None on error.
        """
        # Fetch device statuses from the organization
        try:
            self.org_devices = self.dashboard.organizations.getOrganizationDevicesStatuses(
                self.org_id, total_pages='all'
            )
            print(f"Total devices found: {len(self.org_devices)}")
        except Exception as e:
            print(f"Error fetching device statuses: {e}")
            return None

        # Fetch device details (notes, address) for APs (model starts with 'MR')
        try:
            devices = self.dashboard.organizations.getOrganizationDevices(
                self.org_id, total_pages='all'
            )
            print(f"Total devices found: {len(devices)}")
            for device in devices:
                if device.get('model', '').startswith('MR'):
                    serial = device.get('serial')
                    if serial:
                        self.org_devices_for_loc_check[serial] = device.get('notes', 'Unknown Device')
                        self.org_devices_for_addr_check[serial] = device.get('address', 'Unknown Address')
                        if device.get('notes') == '':
                            self.org_devices_for_loc_check[serial] = 'local'
                        if device.get('address') == '':
                            self.org_devices_for_addr_check[serial] = 'No address'
        except Exception as e:
            print(f"Error fetching device statuses: {e}")
            return None

        # Fetch all networks in the organization
        try:
            networks = self.dashboard.organizations.getOrganizationNetworks(
                self.org_id, total_pages='all'
            )
            print(f"Total networks found: {len(networks)}")
            if not networks:
                print("No networks found in the organization.")
                return None
            self.net = {n['id']: n['name'] for n in networks}
        except Exception as e:
            print(f"Error fetching networks: {e}")
            return None

        # Create mapping of serial -> client count for wireless clients
        for network_id in self.net:
            try:
                clients = self.dashboard.networks.getNetworkClients(network_id, total_pages='all')
                for client in clients:
                    # Check if client is connected to an AP (MR) via wireless
                    if client.get("recentDeviceConnection") == 'Wireless':
                        serial = client.get("recentDeviceSerial")
                        if serial:
                            self.serial_clients_map[serial] = self.serial_clients_map.get(serial, 0) + 1
            except Exception as e:
                print(f"Error fetching clients for network {network_id}: {e}")

        # Build list of APs with normalized information
        for device in self.org_devices:
            if device.get('model', '').startswith('MR'):
                serial = device.get('serial')
                device_info = {
                    'name': device.get('name'),
                    'model': device.get('model'),
                    'description': self.org_devices_for_loc_check.get(serial, 'No description'),
                    'site': self.net.get(device.get('networkId'), 'Unknown Network'),
                    'ip': device.get('lanIp'),
                    'mac': device.get('mac'),
                    'serial': serial,
                    'status': device.get('status'),
                    'current_clients': self.serial_clients_map.get(serial, 0),
                    'address': self.org_devices_for_addr_check.get(serial)
                }
                self.info_org_devices.append(device_info)

        return self.info_org_devices
    
    def change_config_1ap(self, ap_serial: str, config: dict) -> dict:
        """
        Update the configuration of a single AP by its serial number.

        Args:
            ap_serial: The serial number of the AP to configure
            config: Dictionary containing configuration parameters:
                - name: New device name
                - description: New device notes/description
                - address: New physical address

        Returns:
            dict: API response on success, None on error
        """
        try:
            response = self.dashboard.devices.updateDevice(
                ap_serial,
                name=config.get('name'),
                notes=config.get('description'),
                address=config.get('address'),
                tags=['recently-added']
            )
            print(f"AP {ap_serial} configuration updated successfully.")
            return response
        except Exception as e:
            print(f"Error updating AP {ap_serial}: {e}")
            return None

    def config_aps(self, ap_list: list) -> bool:
        """
        Configure multiple APs from a provided list.

        Args:
            ap_list: List of dictionaries containing AP configuration data.
                Each dict should have 'serial', 'name', 'description', 'address' keys.

        Returns:
            bool: True if all configurations succeeded, False on error
        """
        try:
            for ap in ap_list:
                serial = ap.get("serial")
                config = {
                    "name": ap.get("name"),
                    "description": ap.get("description"),
                    "address": ap.get("address")
                }
                self.change_config_1ap(serial, config)
                # Wait 0.5 seconds between configurations to avoid API rate limiting
                sleep(0.5)
            return True
        except Exception as e:
            print(f"Error configuring APs: {e}")
            return False


def main():
    """
    Example usage of the MerakiWLC class.

    Demonstrates how to initialize the client and update AP configuration.
    Replace API_KEY and serial with actual values before running.
    """
    API_KEY = ' '  # Replace with your Meraki API key
    config = {
        "name": "--test-config-ap",
        "description": "Test config AP",
        "address": "Test address"
    }
    serial = " "  # Replace with actual AP serial
    apOrg = MerakiWLC(API_KEY, None)
    apOrg.change_config_1ap(serial, config)
    print(f"AP {serial} configuration updated successfully.")


if __name__ == '__main__':
    main()