import requests
import json
import pandas as pd

url = 'https://hubeau.eaufrance.fr/api/v1/hydrometrie/observations_tr'

params = {
    'fields': 'code_station,grandeur_hydro,date_obs,resultat_obs,libelle_qualification_obs,longitude,latitude',
    'format': 'json',
    'size': 20000,
    'sort': 'desc',
    'date_debut_obs': '2023-10-01',
    'date_fin_obs': '2023-10-09',
    # parisian region
    #'bbox': '48.0,1.0,49.0,3.0',
}

# API call
try:
    api_request = requests.get(url, params=params)
    data = json.loads(api_request.content)
except:
    data = None

# display the data
df = pd.DataFrame(data['data'])
print(df)