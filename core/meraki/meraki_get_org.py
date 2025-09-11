import meraki


class Org:
    """
    Get the all ID organizations  from the Meraki API.
    """

    def __init__(self, meraki_api):
        self.meraki_api = meraki_api

    def get(self):
        # Se obtiene la información de todas las organizaciones
        #  
        responseOK = False
        tries_counter = 0
        array_orgs = None
        orgs = []

        dashboard = meraki.DashboardAPI(self.meraki_api, output_log=False, print_console=False)
        while responseOK == False :
            """
            La solicitud de la información de las organización salta error de forma aleatoria (cosas de Meraki)
            Este While maneja las excepciones y vuelve a intentarlo hasta 10 veces
            """
            try:
                array_orgs = dashboard.organizations.getOrganizations()
                print(":::RESPONSE:::")
                #print(response)
                responseOK = True

                for count, organization in enumerate(array_orgs):
                    clientinfo = (organization['name'], organization['id'])
                    print(clientinfo)
                    orgs.append(clientinfo)
                return orgs
            except :
                print("hubo un error")
                tries_counter + 1
                pass
            if tries_counter > 10:
                responseOK = True
                print("No authorization")
                return 'No authorization'
            
def get_org(meraki_api):
    """
    Get the all ID organizations  from the Meraki API.
    """
    org = Org(meraki_api)
    return org.get()

