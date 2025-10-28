import requests
from pprint import pprint

class SCCD_CI:  
    """Class to interact with SCCD Configuration Items (CI).
     You need to provide SCCD credentials to initialize the class. 
     get_configuration_item need to be called before update_ci_data or change_classstructureid methods to load the CI data.
     """

    def __init__(self, user_sccd, pass_sccd):
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd
        self.url_sccd = 'https://servicedesk.cwc.com/maximo/' 
        self.conf_item_data ={}
        self.session = requests.Session()
        self.patch_headers = {
            'x-method-override': 'PATCH',
            'patchtype': 'MERGE',
            'Content-Type': 'application/json',
            'properties': '*'
        }

    def get_configuration_item(self, cinum):
        ccci_url = f'{self.url_sccd}oslc/os/CCCI'
        params = {
            'lean': '1',
            'oslc.select': 'pluspcustomer,href,cilocation,cilocation,classstructureid,ccipersongroup,cinum',
            'oslc.where': f'cinum="{cinum}"',
        }
        url = requests.PreparedRequest()
        url.prepare_url(ccci_url, params)
        configuration_item_data_url = url.url
        
        try:
            response = self.session.get(configuration_item_data_url, auth=(self.user_sccd, self.pass_sccd))
            if response.status_code == 200:
                configuration_item_data_dic = response.json()
                #Data normalization
                data = configuration_item_data_dic.get('member')[0]
                self.conf_item_data['cinum'] = data.get('cinum', 'N/A')
                self.conf_item_data['cilocation'] = data.get('cilocation', 'N/A')
                self.conf_item_data['classstructureid'] = data.get('classstructureid', 'N/A')
                self.conf_item_data['ccipersongroup'] = data.get('ccipersongroup', 'N/A')
                self.conf_item_data['href'] = data.get('href', 'N/A')+'?lean=1'
                return self.conf_item_data
            else:
                return {"error": "Failed to retrieve configuration item data"}
        except Exception as e:
            return {"error": str(e)}
        

    def get_ap_models(self):
        """Retrieve the list of AP models from SCCD.
        Format output: ["MODEL1", "MODEL2", ...]
        """
        ap_models_url = f'{self.url_sccd}oslc/os/MXDOMAIN'
        params = {
            'lean': '1',
            'oslc.select': 'alndomain',
            'oslc.where': 'domainid="CC_CN_MODEL2"',  
            'oslc.pageSize': '1000'
        }
        url = requests.PreparedRequest()
        url.prepare_url(ap_models_url, params)
        ap_models_data_url = url.url

        try:
            response = self.session.get(ap_models_data_url, auth=(self.user_sccd, self.pass_sccd))
            if response.status_code == 200:
                ap_models_data_dic = response.json()
                ap_models = [item.get('value', 'N/A') for item in ap_models_data_dic.get('member')[0].get('alndomain')]
                return ap_models
            else:
                return {"error": "Failed to retrieve AP models"}
        except Exception as e:
            return {"error": str(e)}

        
    def change_classstructureid(self, new_classstructureid):

        """Change the classstructureid of the configuration item."""

        patch_url = self.conf_item_data.get('href') # Get the href for the configuration item

        if not patch_url:
            return {"error": "Configuration item href not found"}

        patch_payload = {'classstructureid': new_classstructureid}

        try:
            patch_response = self.session.post(patch_url, json=patch_payload,
                                                headers=self.patch_headers,
                                                auth=(self.user_sccd, self.pass_sccd))
            if patch_response.status_code in [200, 204]:
                return {"success": f"Classstructureid updated to {new_classstructureid}"}
            else:
                return {"error": "Failed to update classstructureid"}
        except Exception as e:
            return {"error": str(e)}

    def update_ci_data(self, cispec):

        """Update the configuration item data."""
        data = {'cispec': cispec} # cispec structure: [{assetattrid: "ATTR_ID", value: "NEW_VALUE"}, ...]
        patch_url = self.conf_item_data.get('href')  # Get the href for the configuration item

        if not patch_url:
            return {"error": "Configuration item href not found"}

        try:
            patch_response = self.session.post(patch_url, json=data,
                                                headers=self.patch_headers,
                                                auth=(self.user_sccd, self.pass_sccd))
            if patch_response.status_code in [200, 204]:
                return {"success": "Configuration item updated successfully"}
            else:
                return {"error": "Failed to update configuration item"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    sccd_ci = SCCD_CI("user", "pass")
    ap_models = sccd_ci.get_ap_models()
    pprint(ap_models)
