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
                      owner_by: str = "CW"
                      ):
        """Update the configuration item of a single AP.
        Format of ap_data:

        {"name": "<ap_name>",
        "model": "<ap_model>",
        "description": "<ap_model>",
        "site": "<ap_site>",
        "ip": "<ap_ip>",
        "mac": "<ap_mac>",
        "serial": "<ap_serial>",
        "status": "<ap_status>",
        "current_clients": "<ap_current_clients>",
        "address": "<ap_address>"}

        """

        cid = self.extract_cid_from_ap_name(ap_data.get("name"))
        self.sccd_ci.get_configuration_item(cid)
        if 'error' in self.sccd_ci.conf_item_data:
            return self.sccd_ci.conf_item_data  # Return the error if occurred
        classstructureid = self.sccd_ci.conf_item_data.get('classstructureid')
        if classstructureid != "30019":  # AP classstructureid
            change_response = self.sccd_ci.change_classstructureid("30019")
            if 'error' in change_response:
                return change_response  # Return the error if occurred

            

        
        cispec = [
            {"assetattrid": "ATTRIBUTED", "value": "C&W"},
            {"assetattrid": "SERIAL NUMBER", "value": ap_data.get("serial")},
            {"assetattrid": "HOSTNAME", "value": ap_data.get("hostname")},
            {"assetattrid": "RESOLVED_BY", "value": "C&W"},
            {"assetattrid": "VENDOR", "value": vendor},
            {"assetattrid": "MODEL WIFI", "value": self.model_selector(ap_data.get("model"))}, # Select closest matching model
            {"assetattrid": "MAC ADDRESS", "value": ap_data.get("mac")},
            {"assetattrid": "RELATED CONTROLLER ID", "value": controller},
            {"assetattrid": "VLAN CONTROL", "value": control_vlan},
            {"assetattrid": "DEAL", "value": dealcode},
            {"assetattrid": "MANAGED BY", "value": managed_by}, # options: 'CW', 'Managed Level 2'
            {"assetattrid": "OWNER BY", "value": owner_by}, # options: 'CW', 'CUSTOMER'
            {"assetattrid": "DESCRIPTION/LOCATION", "value": ap_data.get("description")}
        ]
        update_response = self.sccd_ci.update_ci_data(cispec)
        return update_response

    

if __name__ == "__main__":
    devices=["50250279.1.1.CO_AHDSFO_DKDS", "12345678.2.2.US_ADSAI_DSADIS", "87654321.3.3.UK_DSIDI_DIS"]
    sccd_ci = SCCD_CI_Configurator("user", "pass")
    for device in devices:
        ci_data = sccd_ci.extract_cid_from_ap_name(device)
        print(ci_data)
