#!/usr/bin/env python3
"""
Fortigate WiFi Controller API Client.

Requirements:
    pip install requests urllib3

Note:
    TLS verification is temporarily disabled (verify=False).
    Replace with a valid certificate in production environments.
"""

from pprint import pprint
from typing import Dict, List
from time import sleep

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortigateAPI:
    """
    A class to interact with the Fortigate WiFi Controller API.
    """

    def __init__(self, controller_ip: str, api_key: str):
        """
        Initialize the FortigateAPI client.

        Args:
            controller_ip (str): The IP address or hostname of the Fortigate controller.
            api_key (str): The API access token for authentication.
        """
        self.controller_ip = controller_ip
        self.api_key = api_key

    def profile_to_model(self, name: str) -> str:
        """
        Extracts the model number from the AP profile name.

        Removes the first three characters and keeps the substring
        up to the first hyphen "-".

        Args:
            name (str): The AP profile name (e.g., "FAP234F-default").

        Returns:
            str: The extracted model number (e.g., "234F").

        Examples:
            "FAP234F-default"  -> "234F"
            "FAP220B-Oficinas" -> "220B"
        """
        trimmed = name[3:]
        return trimmed.split('-', 1)[0]

    # ---------- AP Query ----------

    def query_aps(self) -> List[Dict]:
        """
        Retrieves the complete list of managed Access Points (APs).

        Uses GET /api/v2/monitor/wifi/managed_ap to fetch AP details.

        Returns:
            List[Dict]: A list of dictionaries, where each dictionary contains
                        details about a managed AP (name, model, IP, status, etc.).
        """
        url = (
            f"https://{self.controller_ip}/api/v2/monitor/wifi/managed_ap"
            f"?vdom=*&access_token={self.api_key}"
        )

        data = requests.get(url, verify=False, timeout=10)
        main_dict = data.json()
        main_dic_results = []
        aps_list_dic: List[Dict] = []
        for vdom_ans in main_dict:
            if len(vdom_ans['results']) > 0:
                main_dic_results.extend(vdom_ans['results'])
        # ---------- Data Formatting ----------
        for ap_data in main_dic_results:
            aps_list_dic.append({
                "name": ap_data['name'],
                "model": self.profile_to_model(ap_data['ap_profile']),
                "description": ap_data['location'],
                "site": 'local',
                "ip": ap_data['local_ipv4_addr'],
                "mac": ap_data['board_mac'],
                "serial": ap_data['serial'],
                "status": ap_data['status'],
                "current_clients": ap_data['clients'],
                "address": 'local'
            })
        print("Reading all APs from Fortigate...")
        pprint(aps_list_dic)
        return aps_list_dic

    def change_config_1ap(self, ap_serial: str, config: Dict):
        """
        Updates the configuration of a specific AP identified by its serial number.

        Args:
            ap_serial (str): The serial number of the AP to update.
            config (Dict): A dictionary containing the configuration parameters to update.

        Returns:
            Dict or None: The JSON response from the API if successful, None otherwise.
        """
        url = (
            f"https://{self.controller_ip}/api/v2/cmdb/wireless-controller/wtp/"
            f"{ap_serial}?vdom=*&access_token={self.api_key}"
        )

        try:
            response = requests.put(url, json=config, verify=False, timeout=10)
            response.raise_for_status()
            print(f"AP {ap_serial} updated successfully")
            return response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error updating AP {ap_serial}: {e}")
            return None

    def config_aps(self, ap_list: List[Dict]):
        """
        Configures a list of APs.

        Iterates through the provided list and updates the configuration
        for each AP based on its serial number.

        Args:
            ap_list (List[Dict]): A list of dictionaries containing AP configuration details.
            Each dict must contain 'serial', 'name', and 'description'.
        """
        for ap in ap_list:
            serial = ap.get("serial")
            config = {
                "name": ap.get("name"),
                "location": ap.get("description")
            }
            self.change_config_1ap(serial, config)
            # Wait 0.5 seconds between configurations to avoid overloading the API
            sleep(0.5)

# ------------------ Direct Execution ------------------ #


if __name__ == "__main__":
    FORTI_CONTROLLER_IP = ""  # FortiGate IP
    FORTI_API_KEY = ""  # API Key

    api = FortigateAPI(FORTI_CONTROLLER_IP, FORTI_API_KEY)
    print("Querying APs from Fortigate...")
    aps = api.query_aps()
    # Example configuration update for the first AP (uncomment to test) 
    print(aps)