"""
SCCD Work Order Connector Module.

This module provides the SCCD class for interacting with the Service Desk (SCCD)
Work Order management system via its REST API.

Provides functionality to:
    - Retrieve work orders assigned to a user
    - Update work order status
    - Add work logs to work orders
    - Add Configuration Items (CIs) to work orders
"""

import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
from bs4 import BeautifulSoup
import html
import re
from datetime import datetime


class SCCD_WO:
    """
    SCCD Work Order management API client.

    Provides methods to connect to SCCD and manage Work Orders including
    status updates, log entries, and CI assignments.

    Attributes:
        owner (str): Work Order owner/assignee username
        user_sccd (str): SCCD login username
        pass_sccd (str): SCCD login password
        url_sccd (str): Base URL for SCCD API
        validate_credentials (Response): Initial credential validation response
        session (requests.Session): HTTP session for API requests
    """

    def __init__(self, owner: str, user_sccd: str, pass_sccd: str):
        """
        Initialize the SCCD client and validate credentials.

        Args:
            owner: Work Order owner/assignee username
            user_sccd: SCCD login username
            pass_sccd: SCCD login password
        """
        self.owner = owner
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd
        self.url_sccd = 'https://servicedesk.cwc.com/maximo/'
        # Validate credentials on initialization
        self.auth = HTTPBasicAuth(self.user_sccd, self.pass_sccd)
        self.validate_credentials = requests.get(self.url_sccd, auth=self.auth)

        self.session = requests.Session()
        self.myheaders = {
            'x-method-override': 'PATCH',
            'patchtype': 'MERGE',
            'Content-Type': 'application/json',
            'properties': '*'
        }

    def get_work_orders(self) -> list | dict:
        """
        Retrieve all work orders assigned to the owner.

        Fetches work orders with status WORKPENDING, INPRG, or QUEUED
        that are not tasks (istask=false).

        Returns:
            list: List of normalized work order dictionaries, with the following keys:
                - wo_id: Work order ID
                - state: Current status of the work order
                - description: Cleaned description of the work order
                - dc: Deal code associated with the work order
                - cids: List of associated Configuration Items (CIs)
                - project_info: Project information extracted from work logs
                - pm: Project manager information extracted from work logs
                - last_update: Latest update from work logs
                - time_min: Time in minutes (default 0)
            dict: Error dictionary if request fails
        """
        url_lref_allwo = (
            f'{self.url_sccd}oslc/os/sidwo?lean=1&oslc.pageSize=60&oslc.select=*'
            f'&oslc.where=owner="{self.owner}"and status IN ["WORKPENDING","INPRG","QUEUED"]and istask=false'
        )
        try:
            response = self.session.get(url_lref_allwo, auth=(self.user_sccd, self.pass_sccd))
            if response.status_code == 200:
                wos_data_dic = response.json()
                wos_data_normalized = SCCD_WO.normalize_work_order_data(wos_data_dic)
                print(f"{len(wos_data_normalized)} workorders are assigned to {self.owner}")
                return wos_data_normalized
            else:
                return {"error": "Failed to retrieve work orders"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def normalize_work_order_data(wo_data_dic: dict) -> list:
        """
        Normalize raw work order data from SCCD API response.

        Extracts and cleans relevant fields from each work order including
        description, CIs, project info, and latest update.

        Args:
            wo_data_dic: Raw work order data dictionary from SCCD API

        Returns:
            list: List of normalized work order dictionaries
        """
        wos_info = []
        for wo_dic in wo_data_dic['member']:
            wo_dic_normalized = {}
            wo_dic_normalized['wo_id'] = wo_dic.get('wogroup', 'N/A')
            wo_dic_normalized['state'] = wo_dic.get('status', 'N/A')
            wo_dic_normalized['description'] = SCCD_WO.text_eraser(wo_dic.get('description', 'N/A'))
            wo_dic_normalized['dc'] = wo_dic.get('wolo2', 'N/A')

            # Extract Configuration Items (CIs)
            cids_list = []
            for cid_dic in wo_dic.get('multiassetlocci', []):
                if cid_dic.get('cinum'):
                    cids_list.append({
                        'cid': cid_dic.get('cinum', 'N/A'),
                        'location': cid_dic.get('location', 'N/A'),
                        'description': SCCD_WO.clean_data(cid_dic.get('targetdesc', 'N/A'))
                    })
            wo_dic_normalized['cids'] = cids_list

            # Extract project info and PM from worklogs
            wo_dic_normalized['project_info'] = "No information"
            wo_dic_normalized['pm'] = "No information"
            for log in wo_dic.get('worklog', []):
                if log.get('description').startswith('P00'):
                    wo_dic_normalized['project_info'] = SCCD_WO.clean_data(log.get('description_longdescription'))
                if log.get('description').startswith('N27'):
                    wo_dic_normalized['pm'] = SCCD_WO.clean_data(log.get('description_longdescription'))

            # Get latest update from worklogs
            wo_dic_normalized['last_update'] = "No information"
            if wo_dic.get('worklog'):
                latest_log = max(wo_dic.get('worklog', []), key=lambda x: datetime.fromisoformat(x['createdate']))
                if latest_log:
                    wo_dic_normalized['last_update'] = SCCD_WO.clean_data(latest_log.get('description_longdescription'))

            wo_dic_normalized['time_min'] = 0
            wos_info.append(wo_dic_normalized)
        return wos_info

    @staticmethod
    def clean_data(raw: str) -> str:
        """
        Clean HTML content from work log entries.

        Removes HTML tags, unescapes HTML entities, and normalizes whitespace.

        Args:
            raw: Raw HTML string from SCCD

        Returns:
            str: Cleaned plain text string
        """
        soup = BeautifulSoup(raw, 'html.parser')
        text = soup.get_text(separator='\n')
        text = html.unescape(text).replace('\xa0', ' ')
        text = '\n'.join(line.rstrip() for line in text.splitlines())
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        return text

    @staticmethod
    def text_eraser(text: str) -> str:
        """
        Remove common keywords and patterns from work order descriptions.

        Strips service-related keywords, country names, and technology terms
        to extract the core project/client name.

        Args:
            text: Raw work order description

        Returns:
            str: Cleaned description with keywords removed
        """
        cleaned_text = text.upper()
        patterns = (
            "-", "(", ")", "NEW SERVICE", "SIDIP", "SID IP", "NEW PROJECT",
            "(SIDIP)", "SID-IP", "NUEVO SERVICIO", "WIFI", "WI-FI", "WI FI",
            "MIGRATION", "MIGRACION", "DEAL ", "SOLUCION", "SOLUTION", "SDWAN",
            "SD-WAN", "ROUTER", "LAN ", "SWITCH", "ACCESS POINT", " AP ", "APS ",
            "FIREWALL", "CISCO", "JUNIPER", "FORTIGATE", "FORTI ", 'MANAGED',
            "ROUTER", "DIA ", "RETAIL ANALYTICS", "DATA WIFI", "DATAWIFI", "NEW ",
            "COLOMBIA", "HONDURAS", "GUATEMALA", "SALVADOR", "TRINIDAD", "JAMAICA",
            "REPUBLICA DOMINICANA", "BARBADOS", "CURAZAO", "PANAMA"
        )
        for pattern in patterns:
            if pattern == "-":
                cleaned_text = cleaned_text.replace(pattern, " ")
            else:
                cleaned_text = cleaned_text.replace(pattern, "")
            cleaned_text = cleaned_text.strip()
        return cleaned_text

    def get_post_url(self, wo_id: str) -> str | dict:
        """
        Get the API endpoint URL for a specific work order.

        Args:
            wo_id: Work order ID (e.g., "WO2018345")

        Returns:
            str: POST URL for the work order, or
            dict: Error dictionary if request fails
        """
        url_lref_wo = f'{self.url_sccd}oslc/os/sidwo?lean=1&oslc.select=*&oslc.where=wonum="{wo_id}"'
        try:
            response_wo = self.session.get(url_lref_wo, auth=(self.user_sccd, self.pass_sccd))
            data_wo = response_wo.json()
            href_post = data_wo['member'][0]['href'] + '?lean=1'
            return href_post
        except Exception as e:
            return {"error": str(e)}

    def update_work_order_state(self, wo_id: str, new_state: str) -> dict:
        """
        Change the status of a work order.

        Args:
            wo_id: Work order ID
            new_state: New status value (e.g., "INPRG", "COMP")

        Returns:
            dict: Success or error message
        """
        try:
            href_post = self.get_post_url(wo_id)
            json_data = {"status": new_state}
            post_response = self.session.post(
                href_post, json=json_data, headers=self.myheaders,
                auth=(self.user_sccd, self.pass_sccd)
            )
            if post_response.status_code in [200, 201]:
                print(f"success, Work order {wo_id} status changed to {new_state}")
                return {"success": f"Work order {wo_id} status changed to {new_state}"}
            else:
                print(f"error, Failed to change status for work order {wo_id}")
                return {"error": f"Failed to change status for work order {wo_id}"}
        except Exception as e:
            return {"error": str(e)}

    def update_work_order_log(self, wo_id: str, log_title: str, log_message: str) -> dict:
        """
        Add a work log entry to a work order.

        Args:
            wo_id: Work order ID
            log_title: Short title/description for the log entry
            log_message: Full log message content

        Returns:
            dict: Success or error message
        """
        try:
            href_post = self.get_post_url(wo_id)
            payload = {
                "worklog": [
                    {
                        "description": log_title,
                        "logtype": "UPDATE",
                        "description_longdescription": log_message
                    }
                ]
            }

            post_response = self.session.post(
                href_post, json=payload, headers=self.myheaders,
                auth=(self.user_sccd, self.pass_sccd)
            )
            if post_response.status_code in [200, 201]:
                print(f"success, log added to work order {wo_id}")
                return {"success": f"Log added to work order {wo_id}"}
            else:
                return {"error": f"Failed to add log to work order {wo_id}"}
        except Exception as e:
            return {"error": str(e)}

    def add_cis_to_work_order(self, wo_id: str, cids: list[dict]) -> dict:
        """
        Add Configuration Items (CIs) to a work order or task.

        Args:
            wo_id: Work order or task ID
            cids: List of CI dictionaries with 'cid' and 'description' keys

        Returns:
            dict: Success or error message
        """
        try:
            href_post = self.get_post_url(wo_id)
            ci_list = [{"cinum": cid["cid"], "targetdesc": cid["description"]} for cid in cids]

            payload = {
                "multiassetlocci": ci_list
            }

            post_response = self.session.post(
                href_post, json=payload, headers=self.myheaders,
                auth=(self.user_sccd, self.pass_sccd)
            )
            if post_response.status_code in [200, 201]:
                print(f"success, {len(cids)} CIs added to {wo_id}")
                return {"success": f"CIs added to work order/task {wo_id}"}
            else:
                return {"error": f"Failed to add CIs to work order/task {wo_id}"}
        except Exception as e:
            return {"error": str(e)}


def main():
    """
    Example usage of the SCCD class.

    Demonstrates how to add CIs to a work order.
    Replace credentials and work order ID before running.
    """
    owner = "owner"  # Work order owner
    user_sccd = "user_sccd"  # SCCD username
    pass_sccd = "pass_sccd"  # SCCD password

    sccd_con = SCCD_WO(owner, user_sccd, pass_sccd)
    cids = [
        {"cid": "8011868.SV", "description": "AP MERAKI"},
        {"cid": "23940535.1.22.SV", "description": "RUCKUS AP"}
    ]

    result = sccd_con.add_cis_to_work_order("WO2018345", cids)
    pprint(result)


if __name__ == "__main__":
    main()
