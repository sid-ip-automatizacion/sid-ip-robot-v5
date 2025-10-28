import re
from typing import List, Tuple
from sccd_ci_connector import SCCD_CI

class SCCD_CI_Configurator:

    def __init__(self, user_sccd, pass_sccd):
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd
        self.sccd_ci = SCCD_CI(user_sccd, pass_sccd)

        self.models_tuples = self.normalize_models(self.sccd_ci.get_ap_models()) # List of tuples (original_model_name, normalized_model_name)


    def normalize_models(self,items: List[str]) -> List[Tuple[str, str]]:
        """
        delete FortiAP, HW, ZoneFlex from model names, remove dashes and spaces, convert to lowercase
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
            if normalized_model in tl[0][1]:
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
        
        The function requieres addional parameters to fill the CI attributes.(vendor, controller, control_vlan, dealcode, managed_by, owner_by, sup_exp)
        """

        cid = self.extract_cid_from_ap_name(ap_data.get("name"))
        print(f"Updating CI for CID: {cid}")
        data = self.sccd_ci.get_configuration_item(cid)
        print(data)
        if 'error' in self.sccd_ci.conf_item_data:
            return self.sccd_ci.conf_item_data  # Return the error if occurred
        classstructureid = self.sccd_ci.conf_item_data.get('classstructureid')
        if classstructureid != "30019":  # AP classstructureid
            change_response = self.sccd_ci.change_classstructureid("30019")
            if 'error' in change_response:
                return change_response  # Return the error if occurred

        
        cispec = [
            {"assetattrid": "ATTRIBUTED", "alnvalue": "C&W"},
            {"assetattrid": "SERIAL NUMBER", "alnvalue": ap_data.get("serial")},
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
        print("CISPEC sent")
        return update_response
    
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
            result = self.update_1ap_ci(ap_data,
                                        vendor,
                                        controller,
                                        control_vlan,
                                        dealcode,
                                        managed_by,
                                        owner_by,
                                        sup_exp)
            
            results.append({ap_data.get("name"): result})
            print(f"SCCD CI updated for AP: {ap_data.get('name')}, Result: {result}")


    

if __name__ == "__main__":
    sccd_ci = SCCD_CI_Configurator("user", "pass")

    ap_info= [{"name": "8011868.SV_CLIENTE1_COMEDOR",
"model": "MR36",
"description": "Comedor",
"site": "Oficina 35",
"ip": "10.20.20.3",
"mac": "00:33:58:0E:71:70",
"serial": "Q3AJ-C3GD-S6VB",
"status": "up-to-date",
"current_clients": "10",
"address": "calle 100 #24"},{"name": "23940535.1.22.SV_CLIENTE1_COMEDOR",
    "model": "MR36",
    "description": "Comedor",
    "site": "Oficina 35",
    "ip": "10.20.20.3",
    "mac": "00:33:58:0E:71:70",
    "serial": "Q3AJ-C3GD-S6VB",
    "status": "up-to-date",
    "current_clients": "10",
    "address": "calle 100 #24"}]

    post_r =sccd_ci.update_multiple_aps_ci(ap_info,
                        vendor="Meraki",
                        controller="Meraki Cloud",
                        control_vlan="20",
                        dealcode="000184236",
                        managed_by="CW",
                        owner_by="CW")
    print(post_r)

