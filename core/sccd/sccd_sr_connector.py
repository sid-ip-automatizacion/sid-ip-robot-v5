import requests
from pprint import pprint


class SCCD_SR:
 
    """ Class use to request location details"""
    
    def __init__(self, user_sccd, pass_sccd):
        self.url_sccd = 'https://servicedesk.cwc.com/maximo/' 
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd
        self.session = requests.Session()

        self.myheaders = {
            'x-method-override': 'PATCH',
            'patchtype': 'MERGE',
            'Content-Type': 'application/json',
            'properties': '*'
        }

    def get_sr_href(self, sr):
        sr_url = f'{self.url_sccd}oslc/os/mxosservreq'
        params = {
            'lean': '1',
            'oslc.select': 'href',
            'oslc.where': f'ticketid="{sr}"',
        }
        url = requests.PreparedRequest()
        url.prepare_url(sr_url, params)
        sr_data_url = url.url

        try:
            response = self.session.get(sr_data_url, auth=(self.user_sccd, self.pass_sccd))
            print(f"Getting info for SR: {sr}")
            if response.status_code == 200 or response.status_code == 201:
                sr_data_dic = response.json()
                href = sr_data_dic['member'][0]['href']+'?lean=1'
                return href
            else:
                return f"Error, Failed to retrieve Service Request data, error code: {response.status_code}"
        except Exception as e:
            return {"error": str(e)}
        
    def add_cis_to_sr(self, sr, cids: list[dict]):
        #Add CIs to Service Request
        try:
            href_post = self.get_sr_href(sr)
            ci_list = [{"cinum": cid["assetnum"], "targetdesc": cid["description"]} for cid in cids]
            jedi = {
                "multiassetlocci": ci_list
            }
            print(jedi)
            post_response = self.session.post(href_post, json=jedi, headers=self.myheaders, auth=(self.user_sccd, self.pass_sccd))
            if post_response.status_code in [200, 201]:
                print(f"success, {len(cids)} CIs added to {sr}")
                return {"success":f"CIs added to Service Request: {sr}"}
            else:
                print(f"error: Failed to add CIs to Service Request: {sr}")
                return {f"error: Failed to add CIs to Service Request: {sr}, error code: {str(post_response.status_code)}"}

        except Exception as e:
            print(e)
            return f"error: {e}"
        
if __name__ == "__main__":
    sccd_sr = SCCD_SR("username", "password")
    sr = "SR12637837"
    cids = [
        {"assetnum": "8011868.SV", "description": "AP MERAKI"},
        {"assetnum": "23940535.1.22.SV", "description": "RUCKUS AP"}
    ]
    response = sccd_sr.add_cis_to_sr(sr,cids)
    print(response)
    