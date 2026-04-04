"""
SCCD_CI_Configurator class used to normalize data and interact with SCCD_CI in sccd_ci_connector.py

"""

import re
from typing import List, Tuple
from time import sleep
from pprint import pprint

from .sccd_ci_connector import SCCD_CI
from .sccd_loc_connector import SCCD_LOC

class SCCD_CI_Configurator:

    """
    Class used to normalize data and interact with SCCD_CI
    """

    def __init__(self, user_sccd, pass_sccd):
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd
        self.sccd_ci = SCCD_CI(user_sccd, pass_sccd)
        self.sccd_loc = SCCD_LOC(user_sccd, pass_sccd)

        self.sw_rt_models = self.sccd_ci.get_rt_sw_models() # Get the list of RT/SW models from SCCD to validate the model in sw_rt_data before updating the CI
        self.models_tuples = self.normalize_models(self.sccd_ci.get_ap_models()) # List of tuples (original_model_name, normalized_model_name)


    def normalize_models(self,items: List[str]) -> List[Tuple[str, str]]:
        """
        delete 'FortiAP', 'HW', 'ZoneFlex' from model names, remove dashes and spaces, convert to lowercase
        :param items: List of model names
        :return: List of tuples (original_model_name, normalized_model_name)
        """

        # Compile regex patterns for removal of unwanted substrings
        patterns = [re.compile(p, re.IGNORECASE) for p in (r'FortiAP', r'HW', r'Zone\s*Flex')]

        out: List[Tuple[str, str]] = []
        for s in items:
            t = s
            for rx in patterns:
                t = rx.sub('', t)
            # Remove dashes and spaces
            t = re.sub(r'[-\s]+', '', t)
            # Lowercase
            t = t.lower()
            out.append((s, t))
        return out

    def model_selector(self, ap_model: str) -> str:
        """Select the closest matching model from SCCD based on the AP model name.
        :param ap_model: The model name of the AP
        :return: The closest matching model name from SCCD
        """
        l = [ap_model]
        tl = self.normalize_models(l)
        # Find the closest match
        for original_model, normalized_model in self.models_tuples:
            if tl[0][1] in normalized_model:
                return original_model
        return "N/A"  # Return N/A if no match found

    def extract_cid_from_ap_name(self, ap_name: str) -> str:
        # Extract the configuration item identifier from the AP name
        CID_PATTERN = re.compile(
            r"""^\s*                # any leading spaces
                (?P<cid>            # group 'cid'
                    \d+             # one or more digits
                    (?:\.\d+)*      # zero or more groups of .digits
                    \.[A-Za-z]{2}   # .CC (country code of 2 letters)
                )
                (?:[_-]|\s|$)       # then comes _ or - or end/space
            """,
            re.VERBOSE,
        )
        if not isinstance(ap_name, str):
            raise TypeError("ap_name should be a string")

        m = CID_PATTERN.match(ap_name)
        if not m:
            raise ValueError(f"No valid CID found in: {ap_name!r}")

        cid = m.group("cid")
        # Normalize the country code to uppercase (last segment after the dot)
        head, country = cid.rsplit(".", 1)
        return f"{head}.{country.upper()}"



    def update_1ap_ci(self, ap_data: dict, 
                      vendor: str,
                      controller: str,
                      control_vlan: str,
                      dealcode: str,
                      managed_by: str = "CW",
                      owner_by: str = "CW",
                      sup_exp: str = "NA"
                      ):
        """Update the configuration item of a single AP.
        Format of ap_data:

        {"name": "<ap_name>",
        "model": "<ap_model>",
        "description": "<ap_description>",
        "site": "<ap_site>",
        "ip": "<ap_ip>",
        "mac": "<ap_mac>",
        "serial": "<ap_serial>",
        "status": "<ap_status>",
        "current_clients": "<ap_current_clients>",
        "address": "<ap_address>"}
        
        The method requieres addional parameters to fill the CI attributes.(vendor, controller, control_vlan, dealcode, managed_by, owner_by, sup_exp)
        When the classstructureid of the CI is not of AP type (30019), it will be changed to that value.
        """

        cid = self.extract_cid_from_ap_name(ap_data.get("name"))
        print(f"Updating CI for CID: {cid}")
        data = self.sccd_ci.get_configuration_item(cid)
        if 'error' in self.sccd_ci.conf_item_data:
            return self.sccd_ci.conf_item_data  # Return the error if occurred
        classstructureid = self.sccd_ci.conf_item_data.get('classstructureid')
        if classstructureid != "30019":  # AP classstructureid
            change_response = self.sccd_ci.change_classstructureid("30019")
            print("Changed classstructureid to 30019 (C&W MANAGED WI-FI AP) for CID: ", cid)
            sleep(2) # Wait for SCCD to process the change
            if 'error' in change_response:
                return change_response  # Return the error if occurred

        
        cispec = [
            {"assetattrid": "ATTRIBUTED", "alnvalue": "C&W"},
            {"assetattrid": "SERIAL NUMBER", "alnvalue": str(ap_data.get("serial"))},
            {"assetattrid": "HOSTNAME", "alnvalue": ap_data.get("name")},
            {"assetattrid": "RESOLVED_BY", "alnvalue": "C&W"},
            {"assetattrid": "VENDOR", "alnvalue": vendor},
            {"assetattrid": "MODEL WIFI", "alnvalue": self.model_selector(ap_data.get("model"))}, # Select closest matching model
            {"assetattrid": "MAC ADDRESS", "alnvalue": ap_data.get("mac")},
            {"assetattrid": "RELATED CONTROLLER ID", "alnvalue": controller},
            {"assetattrid": "VLAN CONTROL", "alnvalue": control_vlan},
            {"assetattrid": "DEAL", "alnvalue": dealcode},
            {"assetattrid": "MANAGED BY", "alnvalue": managed_by}, # options: 'CW', 'Managed Level 2'
            {"assetattrid": "OWNER BY", "alnvalue": owner_by}, # options: 'CW', 'CUSTOMER'
            {"assetattrid": "DESCRIPTION/LOCATION", "alnvalue": ap_data.get("description")},
            {"assetattrid": "SUPPORT CONTRACT EXPIRATION DATE (YYYY-MM-DD)", "alnvalue": sup_exp}
        ]
        update_response = self.sccd_ci.update_ci_data(cispec)
        print(f"{cid} CISPEC sent to SCCD for update")
        return (cid,update_response)
    

    
    def update_multiple_aps_ci(self, aps_data: List[dict],
                             vendor: str,
                             controller: str,
                             control_vlan: str,
                             dealcode: str,
                             managed_by: str = "CW",
                             owner_by: str = "CW",
                             sup_exp: str = "NA"
                             ):
        """Update the configuration items of multiple APs.
        Format of aps_data: List of dictionaries with the same format as in update_1ap_ci.
        """
        results = []
        for ap_data in aps_data:
            print("AP DATA:", ap_data)
            result = self.update_1ap_ci(ap_data,
                                        vendor,
                                        controller,
                                        control_vlan,
                                        dealcode,
                                        managed_by,
                                        owner_by,
                                        sup_exp)
            
            results.append({result[0]: result[1]})
            print(f"SCCD CI updated for AP: {ap_data.get('name')}, Result: {result}")
        print("All APs CI updated in SCCD")
        return results
    
    #managed lan and wan methods

    def update_sw_rt_ci(self, sw_rt_data: dict):
        """Update the configuration item of a switch or router in SCCD.
        Format of sw_rt_data:

        {
        "cid": "<cid>",
        "vendor": "<vendor>",
        "model": "<model>",
        "device_owner": "<device_owner>",
        "sn": "<serial_number>",
        "dcn": ({"ip_dcn": "<ip_dcn>", "vlan_mgmt": "<vlan_mgmt>"}, ...),
        "hostname": "<hostname>",
        "cids_related": ({"cid_related": "<related_cid>", "port": ("related_port>")}, ...),
        "channels": ({"channel_cid": "<channel_cid>", "channel_type": "<channel_type>", "port": "<channel_port>"}, ...),
        "dealcode": "<dealcode>",
        "managed_by": "<managed_by>",
        "device": "<device_type>"
        }
        
        When the classstructureid of the CI as SWITCH is not of SWITCH type (30020), it will be changed to that value.
        When the classstructureid of the CI as ROUTER is not of ROUTER type (30010), it will be changed to that value.

        Location attribute will be filled with the address obtained from SCCD_LOC using the location ID from CI data.



        """
        ip = ""
        vlan_mgmt = ""
        for dcn in sw_rt_data.get("dcn", []):
            if dcn.get("ip_dcn"):
                if ip:
                    ip = ip + " " + dcn.get("ip_dcn")
                else:
                    ip = dcn.get("ip_dcn")
            if dcn.get("vlan_mgmt"):
                if vlan_mgmt:
                    vlan_mgmt = vlan_mgmt + " " + dcn.get("vlan_mgmt")
                else:
                    vlan_mgmt = dcn.get("vlan_mgmt")

        ip_transit_channels = ""
        mpls_channels = ""
        voice_channels = ""
        for channel in sw_rt_data.get("channels", []):
            if channel.get("channel_type") == "ip_transit":
                if ip_transit_channels:
                    ip_transit_channels = ip_transit_channels + " " + channel.get("channel_cid")
                else:
                    ip_transit_channels = channel.get("channel_cid")
            elif channel.get("channel_type") == "mpls":
                if mpls_channels:
                    mpls_channels = mpls_channels + " " + channel.get("channel_cid")
                else:
                    mpls_channels = channel.get("channel_cid")
            elif channel.get("channel_type") == "mpls_voice":
                if voice_channels:
                    voice_channels = voice_channels + " " + channel.get("channel_cid")
                else:
                    voice_channels = channel.get("channel_cid")
        related_cids = ""
        trunk_ports = ""
        for related in sw_rt_data.get("cids_related", []):
            if related.get("cid_related"):
                if related_cids:
                    related_cids = related_cids + " " + related.get("cid_related")
                else:
                    related_cids = related.get("cid_related")
            if related.get("port"):
                ports = "".join(related.get("port")) # Convert tuple of ports to string, due to the format in which ports are sent in sw_rt_data
                if trunk_ports:
                    trunk_ports = trunk_ports + " " + ports
                else:
                    trunk_ports = ports
        license = ""
        if sw_rt_data.get("vendor") == "fortinet":
            license = "EA"
            vendor = "Fortinet"
        if sw_rt_data.get("vendor") == "juniper":
            license = "NA"
            vendor = "Juniper"
        if sw_rt_data.get("vendor") == "cisco":
            license = "NA"
            vendor = "Cisco"

        print("Extracting current CI data from SCCD for CID: ", sw_rt_data.get("cid"))
        self.sccd_ci.get_configuration_item(sw_rt_data.get("cid")) # Get current CI data to check classstructureid and location
        print("Current CI data extracted for CID: ", sw_rt_data.get("cid"))
        cilocation = self.sccd_ci.conf_item_data.get("cilocation")
        loc_result = self.sccd_loc.get_location(cilocation) if cilocation else {"address": "N/A"}
        location = loc_result.get("address", "N/A") if isinstance(loc_result, dict) else "N/A"
        print("Location extracted for CID: ", sw_rt_data.get("cid"), " Location: ", location)

        # Select the matching model from SCCD based on the model name in sw_rt_data, only for RT/SW devices
        model = ""
        print("Selecting model for device")
        if not isinstance(self.sw_rt_models, list):
            return {"error": f"RT/SW models not available: {self.sw_rt_models}"}
        for model_dic in self.sw_rt_models:
            if model_dic.get("description", "").lower() == sw_rt_data.get("model", "").lower():
                model = model_dic.get("model")
                break


        if sw_rt_data.get("device") == "sw":
            """"Update CI for switch device. If classstructureid is not of switch type (30020), it will be changed to that value."""

            classstructureid = "30020"
            
            if 'error' in self.sccd_ci.conf_item_data:
                return self.sccd_ci.conf_item_data  # Return the error if occurred
            current_classstructureid = self.sccd_ci.conf_item_data.get('classstructureid')
            if current_classstructureid != classstructureid:  # SWITCH classstructureid
                change_response = self.sccd_ci.change_classstructureid(classstructureid)
                print("Changed classstructureid to 30020 (C&W MANAGED LAN SWITCH) for CID: ", sw_rt_data.get("cid"))

            cispec = [
                {"assetattrid": "ATTRIBUTED", "alnvalue": "C&W"}, #
                {"assetattrid": "SERIAL NUMBER", "alnvalue": str(sw_rt_data.get("sn"))}, #
                {"assetattrid": "HOSTNAME", "alnvalue": sw_rt_data.get("hostname")}, #
                {"assetattrid": "RESOLVED_BY", "alnvalue": "C&W"}, #
                {"assetattrid": "VENDOR", "alnvalue": vendor}, #
                {"assetattrid": "MODEL IP", "alnvalue": model}, #
                {"assetattrid": "IP DCN", "alnvalue": ip}, #
                {"assetattrid": "VLAN MNGT", "alnvalue": vlan_mgmt}, #
                {"assetattrid": "SERVICE ID IP TRANSIT", "alnvalue": ip_transit_channels}, #
                {"assetattrid": "SERVICE ID MPLS", "alnvalue": mpls_channels}, #
                {"assetattrid": "SERVICE ID MPLS VOICE", "alnvalue": voice_channels}, #
                {"assetattrid": "RELATED SERVICES IDS", "alnvalue": related_cids}, #
                {"assetattrid": "TRUNK PORTS", "alnvalue": trunk_ports}, #
                {"assetattrid": "DEAL", "alnvalue": sw_rt_data.get("dealcode")}, #
                {"assetattrid": "SUPPORT CONTRACT EXPIRATION DATE (YYYY-MM-DD)", "alnvalue": license},#
                {"assetattrid": "MANAGED BY", "alnvalue": sw_rt_data.get("managed_by")}, #
                {"assetattrid": "OWNER BY", "alnvalue": sw_rt_data.get("device_owner")}, #
                {"assetattrid": "LOCATION", "alnvalue": location},
            ]
            
            print("Updating CI data for CID: ", sw_rt_data.get("cid"))
            update_response = self.sccd_ci.update_ci_data(cispec)

            if 'error' in update_response:
                return update_response  # Return the error if occurred
            elif 'success' in update_response:
                print(f"{sw_rt_data.get('cid')} CISPEC sent to SCCD for update")
                return (sw_rt_data.get("cid"),update_response)

        elif sw_rt_data.get("device") == "rt":
            """Update CI for router device. If classstructureid is not of router type (30010), it will be changed to that value."""

            classstructureid = "30010"
            self.sccd_ci.get_configuration_item(sw_rt_data.get("cid"))
            if 'error' in self.sccd_ci.conf_item_data:
                return self.sccd_ci.conf_item_data  # Return the error if occurred
            current_classstructureid = self.sccd_ci.conf_item_data.get('classstructureid')
            if current_classstructureid != classstructureid:  # ROUTER classstructureid
                change_response = self.sccd_ci.change_classstructureid(classstructureid)
                print("Changed classstructureid to 30010 (C&W MANAGED ROUTER) for CID: ", sw_rt_data.get("cid"))
            cispec = [
                {"assetattrid": "ATTRIBUTED", "alnvalue": "C&W"}, #
                {"assetattrid": "SERIAL NUMBER", "alnvalue": str(sw_rt_data.get("sn"))}, #
                {"assetattrid": "HOSTNAME", "alnvalue": sw_rt_data.get("hostname")}, #
                {"assetattrid": "RESOLVED_BY", "alnvalue": "C&W"}, #
                {"assetattrid": "VENDOR_IP", "alnvalue": vendor}, #
                {"assetattrid": "MODEL_NAME", "alnvalue": model}, #
                {"assetattrid": "IP DCN", "alnvalue": ip}, #
                {"assetattrid": "VLAN MNGT", "alnvalue": vlan_mgmt}, #
                {"assetattrid": "SERVICE ID IP TRANSIT", "alnvalue": ip_transit_channels}, #
                {"assetattrid": "SERVICE ID MPLS", "alnvalue": mpls_channels}, #
                {"assetattrid": "SERVICE ID MPLS VOICE", "alnvalue": voice_channels}, #
                {"assetattrid": "RELATED SERVICES IDS", "alnvalue": related_cids}, #
                {"assetattrid": "DEAL", "alnvalue": sw_rt_data.get("dealcode")}, #
                {"assetattrid": "SUPPORT CONTRACT EXPIRATION DATE (YYYY-MM_DD)", "alnvalue": license},#
                {"assetattrid": "MANAGED BY", "alnvalue": sw_rt_data.get("managed_by")}, #
                {"assetattrid": "OWNER BY", "alnvalue": sw_rt_data.get("device_owner")}, #
                {"assetattrid": "LOCATION", "alnvalue": location},
            ]
            print("Updating CI data for CID: ", sw_rt_data.get("cid"))
            print("CISPEC to be sent for update: ")
            pprint(cispec)
            update_response = self.sccd_ci.update_ci_data(cispec)
            if 'error' in update_response:
                return update_response  # Return the error if occurred
            elif 'success' in update_response:
                print(f"{sw_rt_data.get('cid')} CISPEC sent to SCCD for update")
                return (sw_rt_data.get("cid"),update_response)
            
        else:
            return {"error": "Invalid device type, should be 'sw' or 'rt'"}

    def update_multiple_sw_rt_ci(self, sw_rt_data_list: List[dict]):
        """Update the configuration items of multiple switches or routers.
        Format of sw_rt_data_list: List of dictionaries with the same format as in update_sw_rt_ci.
        """
        results = []
        for sw_rt_data in sw_rt_data_list:
            print("SW/RT DATA:", sw_rt_data)
            result = self.update_sw_rt_ci(sw_rt_data)
            results.append({sw_rt_data.get("cid"): result})
            print(f"SCCD CI updated for SW/RT: {sw_rt_data.get('cid')}, Result: {result}")


        


    #backoffice methods

    def put_multiples_ci(self, cids:List[dict]):
        for cid in cids:
            self.sccd_ci.put_ci(cid.get("assetnum"),
                                cid.get("location"),
                                cid.get("classstructureid"),
                                cid.get("pluspcustomer"),
                                cid.get("ccipersongroup"))
        print("All CIs created/updated in SCCD")
        return "success"
    
def test():
    pass
    

if __name__ == "__main__":
    test()

