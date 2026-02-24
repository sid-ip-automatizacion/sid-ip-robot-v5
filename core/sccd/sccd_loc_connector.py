"""
SCCD Location Connector Module.

This module provides the SCCD_LOC class for retrieving location details
from the Service Desk (SCCD) system.
"""

import requests


class SCCD_LOC:
    """
    SCCD Location information retrieval class.

    Provides methods to query location details from SCCD including
    country, customer, and address information.

    Attributes:
        url_sccd (str): Base URL for SCCD API
        user_sccd (str): SCCD login username
        pass_sccd (str): SCCD login password
    """

    def __init__(self, user_sccd: str, pass_sccd: str):
        """
        Initialize the SCCD_LOC client.

        Args:
            user_sccd: SCCD login username
            pass_sccd: SCCD login password
        """
        self.url_sccd = 'https://servicedesk.cwc.com/maximo/'
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd

    def get_location(self, location_id: str) -> dict | str:
        """
        Retrieve location details from SCCD by location ID.

        Args:
            location_id: Location identifier (e.g., "CAJ009-56-L1")

        Returns:
            dict: Normalized location data with keys:
                - country: Country code
                - customer: Customer identifier
                - address: Location address/description
                - location: Original location ID
            str: Error message if request fails
        """
        loc_url = f'{self.url_sccd}oslc/os/cclocations'
        params = {
            'lean': '1',
            'oslc.select': 'cg_loccountry,description,cg_locaddress,pluspcustomer',
            'oslc.where': f'location="{location_id}"',
        }
        url = requests.PreparedRequest()
        url.prepare_url(loc_url, params)
        location_data_url = url.url

        try:
            response = requests.get(location_data_url, auth=(self.user_sccd, self.pass_sccd))
            print(f"Getting address for {location_id}")
            if response.status_code in [200, 201]:
                location_data_dic = response.json()
                # Data normalization
                data = location_data_dic.get('member')[0]
                data_normalized = {
                    "country": data.get("cg_loccountry", ""),
                    "customer": data.get("pluspcustomer", ""),
                    "address": data.get("description", ""),
                    "location": location_id
                }
                return data_normalized
            else:
                return f"Error, Failed to retrieve location data, error code: {response.status_code}"
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    sccd_loc = SCCD_LOC("", "")
    loc_data = sccd_loc.get_location("CAJ009-56-L1")
    print(loc_data)
