"""
Meraki Organization Retrieval Module.

This module provides functionality to retrieve all organizations accessible
with a given Meraki API key.
"""

import meraki


class Org:
    """
    Meraki Organization retrieval class.

    Provides methods to fetch all organizations accessible with the provided API key.

    Attributes:
        meraki_api (str): Meraki Dashboard API key
    """

    def __init__(self, meraki_api: str):
        """
        Initialize the Org instance.

        Args:
            meraki_api: Meraki Dashboard API key
        """
        self.meraki_api = meraki_api

    def get(self) -> list:
        """
        Retrieve all organizations accessible with the API key.

        Implements retry logic (up to 10 attempts) to handle intermittent
        Meraki API errors.

        Returns:
            list: List of tuples (organization_name, organization_id),
                  or 'No authorization' string on persistent failure
        """
        response_ok = False
        tries_counter = 0
        array_orgs = None
        orgs = []

        dashboard = meraki.DashboardAPI(self.meraki_api, output_log=False, print_console=False)

        while response_ok == False:
            # The organization request may fail randomly (Meraki API quirk)
            # This while loop handles exceptions and retries up to 10 times
            try:
                array_orgs = dashboard.organizations.getOrganizations()
                print(":::RESPONSE:::")
                response_ok = True

                for count, organization in enumerate(array_orgs):
                    clientinfo = (organization['name'], organization['id'])
                    print(clientinfo)
                    orgs.append(clientinfo)
                return orgs
            except Exception:
                print("Error occurred, retrying...")
                tries_counter += 1
                pass

            if tries_counter > 10:
                response_ok = True
                print("No authorization")
                return 'No authorization'


def get_org(meraki_api: str) -> list:
    """
    Factory function to retrieve all organizations from Meraki API.

    Args:
        meraki_api: Meraki Dashboard API key

    Returns:
        list: List of tuples (organization_name, organization_id)
    """
    org = Org(meraki_api)
    return org.get()
