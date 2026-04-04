"""
Meraki Switch Information Module.

This module receives the organization ID and MERAKI API_KEY to retrieve
switch information from the organization.

The module returns the following information for each switch in the organization
as a list of dictionaries [{}, {}, ...]:

    - name: Switch device name
    - model: Switch model number
    - serial: Serial number
    - mac: MAC address
    - status: Connection status
    - lan ip: Local IP address
    - ports up: Number of connected ports / total ports
    - uplink interface: Uplink port identifier
    - uplink descp: Uplink port description
    - uplink lldp info: LLDP neighbor information on uplink
"""

import meraki


class MerakiSWinfo:
    """
    Meraki Switch information retrieval class.

    Provides methods to query switch details including port status and uplink information.

    Attributes:
        API_KEY (str): Meraki Dashboard API key
        org (str): Organization ID
        org_devices (list): List of all organization devices
        switches (list): Processed list of switch information
    """

    def __init__(self):
        """Initialize the MerakiSWinfo instance with empty attributes."""
        self.API_KEY = None  # Meraki API KEY
        self.org = None  # Organization name/ID
        self.org_devices = None
        self.switches = []  # Switch information will be stored here

    def get(self, API_KEY: str, org: str) -> list:
        """
        Retrieve all switches from the organization with detailed port information.

        Args:
            API_KEY: Meraki Dashboard API key
            org: Organization ID to query

        Returns:
            list: List of dictionaries containing switch information, or None on error
        """
        self.API_KEY = API_KEY
        self.org = org

        # Get all devices from the organization
        dashboard = meraki.DashboardAPI(self.API_KEY, output_log=False, print_console=False)

        try:
            self.org_devices = dashboard.organizations.getOrganizationDevicesStatuses(
                self.org, total_pages='all'
            )
        except Exception:
            print('Error accessing organization.\n'
                  'Please verify API access permissions.')
            return None

        # Get information for all devices in the organization
        if self.org_devices:
            for i, device in enumerate(self.org_devices):
                # Check each device to identify switches
                if device['productType'] == 'switch':
                    serial = device['serial']
                    # Request port status for this switch
                    port_status = dashboard.switch.getDeviceSwitchPortsStatuses(serial)
                    num_ports = len(port_status)  # Total number of ports
                    ports_connected = 0
                    uplink = None
                    uplink_description = None
                    lldp_info = None

                    for i, port in enumerate(port_status):
                        # Check each port and count connected ones
                        if port['status'] == 'Connected':
                            ports_connected += 1
                        # Detect uplink port to get additional information
                        if port['isUplink'] == True:
                            print('###  UPLINK DETECTED  ###')
                            print(f'###  port{port["portId"]} for {device["name"]}  ###')
                            uplink = port['portId']
                            # Check if LLDP information is available
                            if 'lldp' in port and 'systemName' in port['lldp']:
                                lldp_info = port['lldp']['systemName']
                            else:
                                lldp_info = 'lldp not enabled'
                            # Get uplink port details for description
                            uplink_info = dashboard.switch.getDeviceSwitchPort(
                                serial, port['portId']
                            )
                            uplink_description = uplink_info['name']

                    # Store relevant switch information
                    self.switches.append({
                        'name': device['name'],
                        'model': device['model'],
                        'serial': device['serial'],
                        'mac': device['mac'],
                        'status': device['status'],
                        'lan ip': device['lanIp'],
                        'ports up': f'{ports_connected}/{num_ports}',
                        'uplink interface': f'port{uplink}',
                        'uplink descp': uplink_description,
                        'uplink lldp info': lldp_info
                    })

        return self.switches


def get_switches(API_KEY: str, org_id: str) -> list:
    """
    Factory function to retrieve Meraki switch information.

    Args:
        API_KEY: Meraki Dashboard API key
        org_id: Organization ID to query

    Returns:
        list: List of dictionaries containing switch information
    """
    sw_info = MerakiSWinfo()
    return sw_info.get(API_KEY, org_id)


def main():
    """
    Example usage of the MerakiSWinfo class.

    Replace API_KEY and org_id with actual values before running.
    """
    API_KEY = ' '  # Meraki API Key
    org_id = ' '  # Meraki Organization ID

    sw_info = MerakiSWinfo()
    info = sw_info.get(API_KEY, org_id)
    print(info)


if __name__ == '__main__':
    main()
