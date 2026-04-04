#!/usr/bin/env python3
"""
Ruckus SmartZone Controller API Client.

Requirements:
    pip install requests urllib3

Note:
    TLS verification is temporarily disabled (verify=False).
    Not recommended for production environments.
"""

import requests
import urllib3
from pprint import pprint
from typing import Dict, List
from time import sleep

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SmartZoneAPI:
    """
    Ruckus SmartZone API client.

    Provides methods to authenticate, query domains, retrieve and configure
    Access Points from a SmartZone controller.

    Attributes:
        base_url (str): Base URL for the SmartZone API
        username (str): Authentication username
        password (str): Authentication password
        session (requests.Session): HTTP session with authentication headers
        token (str): Authentication token
    """

    def __init__(self, controller_url: str, username: str, password: str):
        """
        Initialize the SmartZoneAPI client and authenticate.

        Args:
            controller_url: IP address or hostname of the SmartZone controller
            username: Login username
            password: Login password
        """
        self.base_url = f'https://{controller_url}/wsg/api/public/v9_1'
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = self.login()

    def login(self) -> str:
        """
        Authenticate with the SmartZone controller.

        Returns:
            str: Authentication token

        Raises:
            requests.HTTPError: If authentication fails
        """
        url = f'{self.base_url}/session'
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(url, json=payload, verify=False)
        response.raise_for_status()
        token = response.json().get('token')
        self.session.headers.update({'Authorization': f'Session {token}'})
        return token

    # ---------- Domain Queries ----------

    def get_domains(self) -> List[tuple]:
        """
        Retrieve all domains from the SmartZone controller.

        Returns:
            list: List of tuples (domain_name, domain_id)
        """
        url = f'{self.base_url}/domains'
        response = self.session.get(url, verify=False)
        response.raise_for_status()
        domains_data = response.json().get('list', [])
        domains_list_dic = []
        for domain in domains_data:
            domains_list_dic.append((domain.get('name'), domain.get('id')))

        return domains_list_dic

    # ---------- AP Queries ----------

    def query_aps_by_domain(self, domain_id: str,
                            page_size: int = 100) -> List[Dict]:
        """
        Retrieve the complete list of APs within a domain using pagination.

        Uses POST /query/ap endpoint with pagination support.

        Args:
            domain_id: Domain ID to filter APs. Use '0' for all domains.
            page_size: Number of APs to retrieve per page (default: 100)

        Returns:
            list: List of dictionaries containing AP information
        """
        print("Domain:", domain_id)
        endpoint = f"{self.base_url}/query/ap"
        page = 1
        aps: List[Dict] = []
        aps_list_dic: List[Dict] = []

        while True:
            if domain_id == '0':
                payload = {
                    "page": page,
                    "limit": page_size
                }
            else:
                payload = {
                    "filters": [
                        {"type": "DOMAIN", "value": domain_id, "operator": "eq"}
                    ],
                    "page": page,
                    "limit": page_size
                }

            resp = self.session.post(endpoint, json=payload,
                                     verify=False, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            aps.extend(data.get("list", []))

            # Check if we have received all records
            total = data.get("totalCount", len(aps))
            if len(aps) >= total:
                break
            page += 1

        # ---------- Data Formatting ----------
        # Extract and normalize the requested fields from the response
        for ap in aps:
            aps_list_dic.append({
                "name": ap.get("deviceName"),
                "model": ap.get("model"),
                "description": ap.get("description"),
                "site": ap.get("apGroupName"),
                "ip": ap.get("ip"),
                "mac": ap.get("apMac"),
                "serial": ap.get("serial"),
                "status": ap.get("configurationStatus"),
                "current_clients": ap.get("numClients"),
                "address": ap.get("location")
            })
        return aps_list_dic

    # ---------- AP Configuration ----------

    def change_config_1ap(self, ap_mac: str, config: Dict) -> None:
        """
        Update the configuration of a single AP by its MAC address.

        Args:
            ap_mac: MAC address of the AP to configure
            config: Dictionary containing configuration parameters:
                - name: New device name
                - description: New description
                - location: New physical location/address

        Raises:
            requests.HTTPError: If the API request fails
        """
        endpoint = f"{self.base_url}/aps/{ap_mac}"
        response = self.session.patch(endpoint, json=config, verify=False)
        response.raise_for_status()
        print(f"AP {ap_mac} configuration updated successfully.")

    def config_aps(self, ap_list: List[Dict]) -> None:
        """
        Configure multiple APs from a provided list.

        Args:
            ap_list: List of dictionaries containing AP configuration data.
                Each dict should have 'mac', 'name', 'description', 'address' keys.
        """
        for ap in ap_list:
            mac = ap.get("mac")
            config = {
                "name": ap.get("name"),
                "description": ap.get("description"),
                "location": ap.get("address")
            }
            self.change_config_1ap(mac, config)
            # Wait 0.5 seconds between configurations to avoid API rate limiting
            sleep(0.5)
        self.session.close()

    def close(self) -> None:
        """
        Close the session and invalidate the authentication token.
        """
        self.session.close()
        self.token = None


# ------------------ Direct Execution ------------------ #


def main():
    """
    Example usage of the SmartZoneAPI class.

    Replace controller_ip, username, password, and mac with actual values
    before running.
    """
    controller_ip = " "  # SmartZone IP address
    username = " "  # Login username
    password = " "  # Login password
    api = SmartZoneAPI(controller_ip, username, password)
    mac = " "  # AP MAC address
    config = {
        "name": " ",
        "description": " ",
        "location": " "
    }

    api.change_config_1ap(mac, config)


if __name__ == "__main__":
    main()
