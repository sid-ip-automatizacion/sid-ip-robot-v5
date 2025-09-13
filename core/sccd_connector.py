
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
from bs4 import BeautifulSoup
import html, re
from datetime import datetime



class SCCD:

    def __init__(self, owner, user_sccd, pass_sccd):
        self.owner = owner
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd
        self.url_sccd = 'https://servicedesk.cwc.com/maximo/' 
        #The following two lines just validate the credentials
        self.auth = HTTPBasicAuth(self.user_sccd, self.pass_sccd) # Basic Authentication
        self.validate_credentials = requests.get(self.url_sccd, auth=self.auth) # Validate credentials (200=OK, 401=Unauthorized)

        self.session = requests.Session()
        self.myheaders = {
            'x-method-override': 'PATCH',
            'patchtype': 'MERGE',
            'Content-Type': 'application/json',
            'properties': '*'
        }

    def get_work_orders(self):
        # Get the work orders assigned to the user
        url_lref_allwo = '{init_url}oslc/os/sidwo?lean=1&oslc.pageSize=60&oslc.select=*&oslc.' \
                         'where=owner="{uname}"and status IN ["WORKPENDING","INPRG","QUEUED"]and istask=false'. \
            format(init_url=self.url_sccd, uname=self.owner)
        try:
            response = self.session.get(url_lref_allwo, auth=(self.user_sccd, self.pass_sccd))
            if response.status_code == 200:
                wos_data_dic = response.json()
                wos_data_normalized = SCCD.normalize_work_order_data(wos_data_dic)
                return wos_data_normalized
            else:
                return {"error": "Failed to retrieve work orders"}
        except Exception as e:
            return {"error": str(e)}
        

    @staticmethod
    def normalize_work_order_data(wo_data_dic):
        # Normalize work order data
        wos_info = []
        for wo_dic in wo_data_dic['member']:
            wo_dic_normalized={}
            wo_dic_normalized['wo_id'] = wo_dic.get('wogroup', 'N/A')
            wo_dic_normalized['state'] = wo_dic.get('status', 'N/A')
            wo_dic_normalized['description'] = SCCD.text_eraser(wo_dic.get('description', 'N/A'))
            wo_dic_normalized['dc'] = wo_dic.get('wolo2', 'N/A')
            cids_list = []
            for cid_dic in wo_dic.get('multiassetlocci', []):
                if cid_dic.get('cinum'):
                    cids_list.append({'cid': cid_dic.get('cinum', 'N/A'),
                                      'location': cid_dic.get('location', 'N/A'),
                                      'description': SCCD.clean_data(cid_dic.get('targetdesc', 'N/A'))
                                      })
            wo_dic_normalized['cids'] = cids_list
            wo_dic_normalized['project_info'] = "No information"
            for log in wo_dic.get('worklog', []):
                if log.get('description').startswith('P00'):
                    wo_dic_normalized['project_info'] = SCCD.clean_data(log.get('description_longdescription'))
            wo_dic_normalized['last_update'] = "No information"
            if wo_dic.get('worklog'):
                latest_log = max(wo_dic.get('worklog', []), key=lambda x: datetime.fromisoformat(x['createdate']))
                if latest_log:
                    wo_dic_normalized['last_update'] = SCCD.clean_data(latest_log.get('description_longdescription'))
            wo_dic_normalized['time_min'] = 0
            wos_info.append(wo_dic_normalized)
        return wos_info
    
    @staticmethod
    def clean_data(raw):
        # Clean the HTML log
        soup = BeautifulSoup(raw, 'html.parser')
        # get_text with line separator between blocks
        text = soup.get_text(separator='\n')
        text = html.unescape(text).replace('\xa0', ' ')
        text = '\n'.join(line.rstrip() for line in text.splitlines())
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        return text
    
    @staticmethod
    def text_eraser(text: str) -> str:
        # Remove specific patterns from WO description
        cleaned_text = text.upper()
        patterns= ("-", "(", ")", "NEW SERVICE", "SIDIP", "SID IP","NEW PROJECT", "(SIDIP)", "SID-IP", "NUEVO SERVICIO", "WIFI", "WI-FI", "WI FI", "MIGRATION", "MIGRACION",
                            "DEAL", "SOLUCION", "SOLUTION", "SDWAN", "SD-WAN", "ROUTER", "LAN","SWITCH","ACCESS POINT", " AP ", "APS",
                            "FIREWALL", "CISCO", "JUNIPER", "FORTIGATE", "FORTI", 'MANAGED', "ROUTER", "DIA", "RETAIL ANALYTICS",
                            "DATA WIFI", "DATAWIFI", "NEW ",
                              "COLOMBIA", "HONDURAS", "GUATEMALA", "SALVADOR", "TRINIDAD", "JAMAICA", "REPUBLICA DOMINICANA", "BARBADOS", "CURAZAO", "PANAMA")
        for pattern in patterns:
            if pattern == "-":
                cleaned_text = cleaned_text.replace(pattern, " ")
            else:
                cleaned_text = cleaned_text.replace(pattern, "")
            cleaned_text = cleaned_text.strip()
        return cleaned_text
    
    def get_post_url(self, wo_id):
        # Get the URL for making POST requests to the specific work order
        url_lref_wo = '{init_url}oslc/os/sidwo?lean=1&oslc.select=*&oslc.where=wonum="{wo_id}"'.format(init_url=self.url_sccd, wo_id=wo_id)
        try:
            response_wo = self.session.get(url_lref_wo, auth=(self.user_sccd, self.pass_sccd))
            data_wo = response_wo.json()
            href_post = data_wo['member'][0]['href']+'?lean=1'
            return href_post
        except Exception as e:
            return {"error": str(e)}

    def update_work_order_state(self, wo_id, new_state):
        # Change the status of the work order
        try:
            href_post = self.get_post_url(wo_id)
            json={"status": new_state}
            post_response = self.session.post(href_post, json=json, headers=self.myheaders, auth=(self.user_sccd, self.pass_sccd))
            if post_response.status_code in [200, 201]:
                return {"success": f"Work order {wo_id} status changed to {new_state}"}
            else:
                return {"error": f"Failed to change status for work order {wo_id}"}
        except Exception as e:
            return {"error": str(e)}

    def update_work_order_log(self, wo_id, log_title, log_message):
        # Add a log to the work order in SCCD
        try:
            href_post = self.get_post_url(wo_id)
            jedi = {
                "worklog": [
                    {
                        "description": "" + log_title,
                        "logtype": "UPDATE",
                        "description_longdescription": "" + log_message
                    }
                ]
            }

            post_response = self.session.post(href_post, json=jedi, headers=self.myheaders, auth=(self.user_sccd, self.pass_sccd))
            if post_response.status_code in [200, 201]:
                return {"success": f"Log added to work order {wo_id}"}
            else:
                return {"error": f"Failed to add log to work order {wo_id}"}
        except Exception as e:
            return {"error": str(e)}


def main(): 
    owner = " "  # user
    user_sccd = " "  # SCCD user
    pass_sccd = " "  # SCCD password

    sccd_con = SCCD(owner, user_sccd, pass_sccd)
    data=sccd_con.get_work_orders()
    pprint(data)




if __name__ == "__main__":

    main()