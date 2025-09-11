#!/usr/bin/env python3
"""
Requisitos:
    pip install requests urllib3
Nota: Se deshabilita temporalmente la verificación TLS (verify=False).
      Sustitúyelo por un certificado válido en producción.
"""
import requests
import urllib3
from pprint import pprint
from typing import Dict, List
from time import sleep

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortigateAPI:
    def __init__(self, controller_ip, api_key):
        self.controller_ip = controller_ip
        self.api_key = api_key

    # ---------- Consulta de APs ----------
    def query_aps(self, page_size: int = 100) -> List[Dict]:
        """
        Devuelve la lista completa de APs
        usando POST /query/ap y paginación.
        """
        url = "https://{fIP}/api/v2/monitor/wifi/managed_ap?" \
                      "vdom=*&access_token={key}".format(fIP=self.controller_ip, key=self.api_key)
        
        requests.packages.urllib3.disable_warnings()
        data = requests.get(url, verify=False)
        print("request response code : .............................. ", data.status_code)
        main_dict = data.json()
        main_dic_results = []
        aps_list_dic: List[Dict] = []
        for vdom_ans in main_dict:
            if len(vdom_ans['results']) > 0:
                main_dic_results.extend(vdom_ans['results'])
        # ---------- Formateo de datos ----------
        for ap in range(len(main_dic_results)):
            aps_list_dic.append(
                {"name": main_dic_results[ap]['name'],
                "model": main_dic_results[ap]['os_version'],
                "description": main_dic_results[ap]['location'],
                "site": 'local',
                "mac": main_dic_results[ap]['board_mac'],
                "ip": main_dic_results[ap]['local_ipv4_addr'],
                "serial": main_dic_results[ap]['serial'],
                "status": main_dic_results[ap]['status'],
                "current_clients": main_dic_results[ap]['clients'],
                "address": 'local'}
                )
        print("lee todos los aps del fortigate")
        pprint(aps_list_dic)
        return aps_list_dic

    def change_config_1ap(self, ap_serial: str, config: Dict):
        """
        Cambia la configuración de un AP dado su serial.
        """
        url = "https://{fIP}/api/v2/cmdb/wireless-controller/wtp/{serial}?vdom=*&access_token={key}".format(
            fIP=self.controller_ip, serial=ap_serial, key=self.api_key)
        
        try:
            requests.packages.urllib3.disable_warnings()
            response = requests.put(url, json=config, verify=False)
            response.raise_for_status()
            print(f"Configuración del AP {ap_serial} actualizada correctamente.")
            return response.json()
        except Exception as e:
            print(f"Error updating AP {ap_serial}: {e}")
            return None

    def config_aps(self, ap_list: List[Dict]):
        """
        Configura los APs en la lista proporcionada.
        """
        for ap in ap_list:
            serial = ap.get("serial")
            config = {
                "name": ap.get("name"),
                "location": ap.get("description")
            }
            self.change_config_1ap(serial, config)
            # Espera 0.5 segundos entre configuraciones para evitar sobrecarga
            sleep(0.5)

# ------------------ Ejecución directa ------------------ #

if __name__ == "__main__":
    controller_ip = " "  # IP del FortiGate
    api_key = " "  # apikey


    api = FortigateAPI(controller_ip, api_key)

