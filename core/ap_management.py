from pprint import pprint

from .meraki import MerakiWLC
from .ruckus import SmartZoneAPI    
from .fortinet import FortigateAPI




class Controller:
    def __init__(self, vendor):
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
        raise NotImplementedError("Subclase debe implementar método get")

    def put(self):
        raise NotImplementedError("Subclase debe implementar método put")


class MerakiController(Controller):
    def __init__(self, vendor, meraki_api_key, meraki_org_id, ap_list):
        super().__init__(vendor)
        self.meraki_api_key = meraki_api_key
        self.meraki_org_id = meraki_org_id
        self.ap_list = ap_list

    def get(self):
        controller = MerakiWLC(self.meraki_api_key, self.meraki_org_id)
        self.ap_list = controller.get()
        return self.ap_list

    def put(self):
        controller = MerakiWLC(self.meraki_api_key, self.meraki_org_id)
        if self.ap_list:
            controller.config_aps(self.ap_list)
            return True
        else:
            print("No APs to configure.")
            return False
    
class FortiController(Controller):
    def __init__(self, vendor, url, forti_key, ap_list):
        super().__init__(vendor)
        self.url = url
        self.forti_key = forti_key
        self.ap_list = ap_list

    def get(self):
        controller = FortigateAPI(self.url, self.forti_key)
        self.ap_list = controller.query_aps()
        return self.ap_list

    def put(self):
        controller = FortigateAPI(self.url, self.forti_key)
        if self.ap_list:
            controller.config_aps(self.ap_list)
            return True
        else:
            print("No APs to configure.")
            return False


class RuckusController(Controller):
    def __init__(self, vendor, login_url, domain_id, login_user, login_password, ap_list):
        super().__init__(vendor)
        self.login_user = login_user
        self.login_password = login_password
        self.login_url = login_url
        self.ruckus_domain_id = domain_id
        self.ap_list = ap_list

    def get(self):
        controller = SmartZoneAPI(self.login_url, self.login_user, self.login_password)
        self.ap_list = controller.query_aps_by_domain(self.ruckus_domain_id)
        return self.ap_list

    def put(self):
        controller = SmartZoneAPI(self.login_url, self.login_user, self.login_password)
        if self.ap_list:
            controller.config_aps(self.ap_list)
            return True
        else:
            print("No APs to configure.")
            return False
    


# Factory function to create the appropriate controller based on the vendor
class ControllerFactory:
    @staticmethod
    def create_controller(controller_info):
        vendor = controller_info["vendor"]
        if vendor == "meraki":
            return MerakiController(controller_info["vendor"],
                                   controller_info["meraki_api_key"],
                                   controller_info["meraki_org_id"],
                                   controller_info["ap_list"])
        elif vendor == "forti":
            return FortiController(controller_info["vendor"],
                                   controller_info["login_url"],
                                   controller_info["forti_key"],
                                   controller_info["ap_list"])
        elif vendor == "ruckus":
            return RuckusController(controller_info["vendor"],
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
    print("AP List:" )  # Debugging line to check the AP list
    pprint(ap_list)  # Print the AP list in a readable format

if __name__ == "__main__":
    """
    Initialize the module.
    """
    main()
