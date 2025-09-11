from .ruckus_sz_controller import SmartZoneAPI

def get_domains(controller_ip, username, password):
    api = SmartZoneAPI(controller_ip, username, password)
    return api.get_domains()