import requests
import streamlit as st
from streamlit_folium import folium_static
import json
import pandas as pd
import folium
import geopandas as gpd

url = "http://environment.data.gov.uk/flood-monitoring/id/floods"

params = {
    #"lat": 51.507581,
    #"long": -0.127597,
    #"distance": 5,
}

#Requette
try:
    api_request = requests.get(url, params=params)
    data = json.loads(api_request.content)
except Exception as e:
    data = "Error..."

df = pd.DataFrame(data["items"])
columns_to_drop = ['eaRegionName', 'isTidal', 'timeSeverityChanged', 'timeMessageChanged']
df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
df['floodArea'] = df['floodArea'].apply(lambda x: x['polygon'] if 'polygon' in x else None)
last_hour = df[df['severityLevel'].isin([1, 2,3,4])].sort_values(by=['timeRaised']).tail(10)
last_hour.head()



m = folium.Map(location=[53.5, -1.5], zoom_start=6)

for x in last_hour['floodArea']:
    # fichier geojson contenant le polygon
    geojson_file = x
    gdf = gpd.read_file(geojson_file)

    # ajout du polygon sur la carte avec la couleur correspondant au niveau d'alerte (jaune ou rouge) avec bordure de la même couleur
    if last_hour['severityLevel'].iloc[0] == 1:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'green', 'color': 'green'}).add_to(m)
    elif last_hour['severityLevel'].iloc[0] == 2:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'yellow', 'color': 'yellow'}).add_to(m)
    elif last_hour['severityLevel'].iloc[0] == 3:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'orange', 'color': 'orange'}).add_to(m)
    elif last_hour['severityLevel'].iloc[0] == 4:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'red', 'color': 'red'}).add_to(m)
    else:
        folium.GeoJson(gdf).add_to(m)

st.write(""" # MyFirstApp  Hello word""")
st.title('Carte Folium dans Streamlit')
folium_static(m)


