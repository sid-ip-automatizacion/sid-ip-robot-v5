import meraki

"""
Ese módulo recibe la organización, y el MERAKI API_KEY
El módulo regresa la iguiente información de los SW del organización en formato [{},{}...]

	Nombre
	Modelo
	Serial
	MAC
    Estado
	IP local
	Cuántos puertos tiene y cuántos están arriba.
	cuál es el uplink
    Descripción del uplink
    LLDP info dle uplink
   
"""


class MerakiSWinfo:

    def __init__(self):

        self.API_KEY = None # Meraki API KEY
        self.org = None # Nombre de la org
        self.org_devices = None
        self.switches = [] # aquí irá la información de los SW

    def get(self, API_KEY, org):
        self.API_KEY = API_KEY
        self.org = org

        #Se obtienen todos los equipos de la organización
        dashboard = meraki.DashboardAPI(self.API_KEY, output_log=False, print_console=False)

        try:
            self.org_devices = dashboard.organizations.getOrganizationDevicesStatuses(
                self.org, total_pages='all'
            )
        except:
            print('Error intentando acceder a la organización \n'
            'Se sugire revisar accesos')
            return None
        #Se obtiene información de todos los equipos de la organización
        
        if self.org_devices:

            for i, device in enumerate(self.org_devices):
            #Se revisa cada equipo para detectar cuál es SW
                if device['productType']=='switch':
                    serial=device['serial']
                    #Se realiza solitud para revisar el estado de los puertos del SW
                    port_status=dashboard.switch.getDeviceSwitchPortsStatuses(serial)
                    num_ports=len(port_status) #¿cuántos puertos hay?
                    ports_connected=0
                    uplink = None
                    uplink_description = None
                    lldp_info = None
                    
                    for i, port in enumerate(port_status):

                        #Se revisa cada puerto y se detecta los que están arriba
                        if port['status']=='Connected':
                            ports_connected += 1
                        #Se detecta el uplink para obtener información
                        if port['isUplink']==True:
                            print('###  UPLINK DETECTED  ###')
                            print(f'###  port{port['portId']} for {device['name']}  ###')
                            uplink = port['portId']
                            # Se valida si hay lldp key
                            if  'lldp' in port and 'systemName' in port['lldp']:
                                lldp_info = port['lldp']['systemName']
                            else:
                                lldp_info = 'lldp not enabled'
                            #Se consulta el detalle del uplink para saber la descripción
                            uplink_info = dashboard.switch.getDeviceSwitchPort(
                                serial, port['portId']
                            )
                            uplink_description = uplink_info['name']

                    #Se guarda información de interés
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
                    

def get_switches(API_KEY, org_id):
    """
    Función para obtener la información de los switches Meraki.
    Recibe el API_KEY y el ID de la organización.
    Retorna una lista de diccionarios con la información de los switches.
    """
    plustec = MerakiSWinfo()
    return plustec.get(API_KEY, org_id)





def main():
    API_KEY = ' '  # Meraki API Key
    org_id = ' '  # ID de la organización Meraki

    plustec = MerakiSWinfo()
    info=plustec.get(API_KEY, org_id)
    print(info)
    

if __name__ == '__main__':
    main()