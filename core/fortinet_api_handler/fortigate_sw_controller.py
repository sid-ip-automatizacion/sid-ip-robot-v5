"""
Fortigate Switch Controller API Handler

"""

import requests
import urllib3
from pprint import pprint

from .fortiswitch_extractor import extraer_fortiswitches


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortigateSWController:
    """
    A class to interact with the Fortigate Switch Controller API.
    """

    def __init__(self, controller_ip: str, api_key: str):
        """
        Initialize the FortigateSWController client.

        Args:
            controller_ip (str): The IP address or hostname of the Fortigate switch controller.
            api_key (str): The API access token for authentication.
        """
        self.controller_ip = controller_ip
        self.api_key = api_key

    def get_switches(self) -> list:
        """
        Fetches the list of switches from the Fortigate switch controller.

        Returns:
            list: A list of switches with their details.
        """
        url = (
            f"https://{self.controller_ip}/api/v2/monitor/switch-controller/managed-switch/status"
            f"?vdom=*&access_token={self.api_key}"
        )

        data = requests.get(url, verify=False, timeout=10)
        normalized_data = extraer_fortiswitches(data.json())
        return normalized_data



def main():
    controller_ip = ""
    api_key = ""
    
    fgt = FortigateSWController(controller_ip, api_key)
    switches = fgt.get_switches()
    pprint(switches)

if __name__ == "__main__":
    main()