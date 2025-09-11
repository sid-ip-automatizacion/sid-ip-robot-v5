import meraki
from time import sleep
from pprint import pprint

"""
Ese módulo recibe la organización (org_id), y el MERAKI API_KEY para obtener información de los puntos de acceso (AP) de la organización.
El módulo regresa la siguiente información de cada AP del organización en formato [{},{}...]

    Nombre
    model
    description
    network name
    MAC address
    local IP 
    serial
    status
    current clients

Pending: fix  getOrganizationDevicesStatuses (Deprecated: This operation has been marked as deprecated, which means it could be removed at some point in the future.)
"""
class MerakiWLC:
    def __init__(self, api_key, org_id):
        self.api_key = api_key
        self.org_id = org_id
        self.net = {}
        self.org_devices = []
        self.org_devices_for_loc_check = {}
        self.org_devices_for_addr_check = {}
        self.info_org_devices = []
        self.serial_clients_map = {}  # Mapeo de serial a número de clientes conectados
        self.dashboard = meraki.DashboardAPI(api_key, output_log=False, print_console=False)

    def get(self):
        try:
            self.org_devices = self.dashboard.organizations.getOrganizationDevicesStatuses(
                self.org_id, total_pages='all'
            )
            print(f"Total devices found: {len(self.org_devices)}") # Debugging line
        except Exception as e:
            print(f"Error fetching device statuses: {e}")
            return None

        try:
            devices = self.dashboard.organizations.getOrganizationDevices(
                self.org_id, total_pages='all'
            )
            print(f"Total devices found: {len(devices)}") # Debugging line
            for device in devices:
                if device.get('model', '').startswith('MR'):
                    serial = device.get('serial')
                    if serial:
                        self.org_devices_for_loc_check[serial] = device.get('notes', 'Unknown Device')
                        self.org_devices_for_addr_check[serial] = device.get('address', 'Unknown Address')
                        if device.get('notes')== '':
                            self.org_devices_for_loc_check[serial] = 'local'
                        if device.get('address')== '':
                            self.org_devices_for_addr_check[serial] = 'No address'
        except Exception as e:
            print(f"Error fetching device statuses: {e}")
            return None


        try:
            networks = self.dashboard.organizations.getOrganizationNetworks(
                self.org_id, total_pages='all'
            )
            print(f"Total networks found: {len(networks)}")  # Debugging line
            if not networks:
                print("No networks found in the organization.")
                return None
            self.net = {n['id']: n['name'] for n in networks}
        except Exception as e:
            print(f"Error fetching networks: {e}")
            return None
        


        # Crear un mapeo de serial -> número de clientes
        

        for network_id in self.net:
            try:
                clients = self.dashboard.networks.getNetworkClients(network_id, total_pages='all')
                for client in clients:
                    # Validar si el cliente está conectado a un AP (MR) por el campo 'recentDeviceConnections'
                    if client.get("recentDeviceConnection") == 'Wireless':
                        serial = client.get("recentDeviceSerial")
                        if serial:
                            self.serial_clients_map[serial] = self.serial_clients_map.get(serial, 0) + 1
                #print(f"Network {network_id} ({self.net[network_id]}) has {len(clients)} clients.")
                #print(f"Clients for network {network_id}: {self.serial_clients_map.get(network_id, 0)}")  # Debugging line
            except Exception as e:
                print(f"Error fetching clients for network {network_id}: {e}")

        # Construir lista de APs con información

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
    
    def change_config_1ap(self, ap_serial: str, config: dict):
        """
        Cambia la configuración de un AP dado su serial.
        """
        try:
            response = self.dashboard.devices.updateDevice(ap_serial, name=config.get('name'),
                                                           notes=config.get('description'),
                                                           address=config.get('address'),
                                                           tags=['recently-added'])
            print(f"Configuración del AP {ap_serial} actualizada correctamente.")
            return response
        except Exception as e:
            print(f"Error updating AP {ap_serial}: {e}")
            return None
    def config_aps(self, ap_list):
        """
        Configura los APs en la lista proporcionada.
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
                # Espera 0.5 segundos entre configuraciones para evitar sobrecarga
                sleep(0.5)
            return True
        except Exception as e:
            print(f"Error configuring APs: {e}")
            return False


def main():
    """
    
    org_id = ''

    apOrg = MerakiWLC(API_KEY, org_id)
    info = apOrg.get()
    pprint(info)
    """
    API_KEY = ' '
    config = {
        "name": "--test-config-ap",
        "description": "Test config AP",
        "address": "Test address"
    }
    serial = " "
    apOrg = MerakiWLC(API_KEY, None)
    apOrg.change_config_1ap(serial, config)
    print("Configuración del AP {} actualizada correctamente.".format(serial))


if __name__ == '__main__':
    main()