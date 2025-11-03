
import requests


class SCCD_LOC:
 
    """ Class use to request location details"""
    
    def __init__(self, user_sccd, pass_sccd):
        self.url_sccd = 'https://servicedesk.cwc.com/maximo/' 
        self.user_sccd = user_sccd
        self.pass_sccd = pass_sccd

    def get_location(self, location_id):
        loc_url = f'{self.url_sccd}oslc/os/cclocations'
        params = {
            'lean': '1',
            'oslc.select': 'cg_loccountry,description,cg_locaddress,pluspcustomer',
            'oslc.where': f'location="{location_id}"',
        }
        url = requests.PreparedRequest()
        url.prepare_url(loc_url, params)
        location_data_url = url.url

        try:
            response = requests.get(location_data_url, auth=(self.user_sccd, self.pass_sccd))
            print(f"Getting address for {location_id}")
            if response.status_code == 200 or response.status_code == 201:
                location_data_dic = response.json()
                #Data normalization
                data = location_data_dic.get('member')[0]
                data_normalized = {}
                data_normalized["country"] = data.get("cg_loccountry", "")
                data_normalized["customer"] = data.get("pluspcustomer", "")
                data_normalized["address"] = data.get("description", "")
                data_normalized["location"] = location_id
                return data_normalized
            else:
                return f"Error, Failed to retrieve location data, error code: {response.status_code}"
        except Exception as e:
            return {"error": str(e)}
        
if __name__ == "__main__":
    sccd_loc = SCCD_LOC("username", "password")
    loc_data = sccd_loc.get_location("CAJ009-56-L1")
    print(loc_data)