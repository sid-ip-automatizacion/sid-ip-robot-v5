"""
AP Management Module

This module provides a unified interface for managing Access Points (APs) across different vendors
(Meraki, Fortinet, Ruckus). It defines a base `Controller` class and vendor-specific implementations
to handle AP configuration and retrieval.
"""

from pprint import pprint

from .meraki import MerakiWLC
from .ruckus import SmartZoneAPI
from .fortinet import FortigateAPI


class Controller:
    """
    Base class for AP Controllers.

    This class defines the interface that all vendor-specific controllers must implement.
    """

    def __init__(self, vendor):
        """
        Initialize the Controller.

        Args:
            vendor (str): The vendor name (e.g., 'meraki', 'forti', 'ruckus').
        """
        self.vendor = vendor
        self.login_user = None
        self.login_password = None
        self.login_url = None
        self.ruckus_domain_id = None
        self.meraki_api_key = None
        self.meraki_org_id = None
        self.forti_key = None
        self.ap_list = None

    def get(self):
        """
        Retrieve the list of APs from the controller.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("get method not implemented")

    def put(self):
        """
        Configure the APs on the controller.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("put method not implemented")


class MerakiController(Controller):
    """
    Controller implementation for Meraki.
    """

    def __init__(self, vendor, meraki_api_key, meraki_org_id, ap_list):
        """
        Initialize the MerakiController.

        Args:
            vendor (str): The vendor name.
            meraki_api_key (str): The API key for Meraki.
            meraki_org_id (str): The Organization ID for Meraki.
            ap_list (list): List of APs to manage.
        """
        super().__init__(vendor)
        self.meraki_api_key = meraki_api_key
        self.meraki_org_id = meraki_org_id
        self.ap_list = ap_list

    def get(self):
        """
        Retrieve APs from Meraki Dashboard.

        Returns:
            list: The list of APs.
        """
        controller = MerakiWLC(self.meraki_api_key, self.meraki_org_id)
        self.ap_list = controller.get()
        return self.ap_list

    def put(self):
        """
        Configure APs on Meraki Dashboard.

        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        controller = MerakiWLC(self.meraki_api_key, self.meraki_org_id)
        if self.ap_list:
            controller.config_aps(self.ap_list)
            return True
        else:
            print("No APs to configure.")
            return False


class FortiController(Controller):
    """
    Controller implementation for Fortinet.
    """

    def __init__(self, vendor, url, forti_key, ap_list):
        """
        Initialize the FortiController.

        Args:
            vendor (str): The vendor name.
            url (str): The URL of the Fortigate controller.
            forti_key (str): The API key for Fortigate.
            ap_list (list): List of APs to manage.
        """
        super().__init__(vendor)
        self.url = url
        self.forti_key = forti_key
        self.ap_list = ap_list

    def get(self):
        """
        Retrieve APs from Fortigate.

        Returns:
            list: The list of APs.
        """
        controller = FortigateAPI(self.url, self.forti_key)
        self.ap_list = controller.query_aps()
        return self.ap_list

    def put(self):
        """
        Configure APs on Fortigate.

        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        controller = FortigateAPI(self.url, self.forti_key)
        if self.ap_list:
            controller.config_aps(self.ap_list)
            return True
        else:
            print("No APs to configure.")
            return False


class RuckusController(Controller):
    """
    Controller implementation for Ruckus SmartZone.
    """

    def __init__(self, vendor, login_url, domain_id, login_user, login_password, ap_list):
        """
        Initialize the RuckusController.

        Args:
            vendor (str): The vendor name.
            login_url (str): The URL of the SmartZone controller.
            domain_id (str): The Domain ID for the APs.
            login_user (str): The username for login.
            login_password (str): The password for login.
            ap_list (list): List of APs to manage.
        """
        super().__init__(vendor)
        self.login_user = login_user
        self.login_password = login_password
        self.login_url = login_url
        self.ruckus_domain_id = domain_id
        self.ap_list = ap_list

    def get(self):
        """
        Retrieve APs from Ruckus SmartZone.

        Returns:
            list: The list of APs.
        """
        controller = SmartZoneAPI(
            self.login_url, self.login_user, self.login_password)
        self.ap_list = controller.query_aps_by_domain(self.ruckus_domain_id)
        return self.ap_list

    def put(self):
        """
        Configure APs on Ruckus SmartZone.

        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        controller = SmartZoneAPI(
            self.login_url, self.login_user, self.login_password)
        if self.ap_list:
            controller.config_aps(self.ap_list)
            return True
        else:
            print("No APs to configure.")
            return False


# Factory function to create the appropriate controller based on the vendor
class ControllerFactory:
    """
    Factory class to create controller instances.
    """
    @staticmethod
    def create_controller(controller_info):
        """
        Create a controller instance based on the provided information.

        Args:
            controller_info (dict): A dictionary containing controller configuration.

        Returns:
            Controller: An instance of a subclass of Controller.

        Raises:
            ValueError: If the vendor is unsupported.
        """
        vendor = controller_info["vendor"]
        if vendor == "meraki":
            return MerakiController(
                controller_info["vendor"],
                controller_info["meraki_api_key"],
                controller_info["meraki_org_id"],
                controller_info["ap_list"])
        elif vendor == "forti":
            return FortiController(
                controller_info["vendor"],
                controller_info["login_url"],
                controller_info["forti_key"],
                controller_info["ap_list"])
        elif vendor == "ruckus":
            return RuckusController(
                controller_info["vendor"],
                controller_info["login_url"],
                controller_info["ruckus_domain_id"],
                controller_info["login_user"],
                controller_info["login_password"],
                controller_info["ap_list"])
        else:
            raise ValueError(f"Unsupported vendor: {vendor}")


def get_controller(controller_info):
    """
    Factory function to create the appropriate controller based on the vendor.

    Args:
        controller_info (dict): A dictionary containing controller configuration.

    Returns:
        Controller: An instance of a subclass of Controller.
    """
    return ControllerFactory.create_controller(controller_info)


def main():
    """
    Main function to demonstrate the usage of the controller module.
    """
    controller_info = {
        "vendor": None,
        "login_user": None,
        "login_password": None,
        "login_url": None,
        "ruckus_domain_id": None,
        "meraki_api_key": None,
        "meraki_org_id": None,
        "forti_key": None,
        "ap_list": None
    }

    controller = get_controller(controller_info)
    ap_list = controller.get()
    print("Controller initialized with vendor:", controller_info["vendor"])
    print("AP List:")  # Debugging line to check the AP list
    pprint(ap_list)  # Print the AP list in a readable format


if __name__ == "__main__":
    """
    Initialize the module.
    """
    # main()
