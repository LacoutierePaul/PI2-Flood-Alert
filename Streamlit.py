#Code

import requests
import streamlit as st
from streamlit_folium import folium_static
import json
import pandas as pd
import folium
import geopandas as gpd

st.write(""" # Pi² 
          Premier Test Streamlit Innondation""")
date=st.date_input("Pick a date")
st.write("You pick : ",date)

url = "http://environment.data.gov.uk/flood-monitoring/id/floods"
params = {
    #'date': date,
    "min-severity" : 3
}

try:
    api_request = requests.get(url, params=params)
    data = json.loads(api_request.content)
except Exception as e:
    data = "Error..."

df = pd.DataFrame(data["items"])
columns_to_drop = ['eaRegionName', 'isTidal', 'timeSeverityChanged', 'timeMessageChanged']
df['floodArea'] = df['floodArea'].apply(lambda x: x['polygon'] if 'polygon' in x else None)
df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
# affichage des alertes sur la derniere heure
df['timeRaised'] = pd.to_datetime(df['timeRaised'])
df['timeRaised'] = df['timeRaised'].dt.date
st.dataframe(df)

filtered_df = df[df['timeRaised'] == date]
# Créer une carte Folium ou tout autre élément de votre application Streamlit
# Afficher le DataFrame filtré dans votre application
st.title(f'Données pour la date {date}')
filtered_df = filtered_df.sort_values(by='severityLevel')
st.dataframe(filtered_df)

m = folium.Map(location=[53.5, -1.5], zoom_start=6)

for x in filtered_df['floodArea'].head(10):
    # fichier geojson contenant le polygon
    geojson_file = x
    gdf = gpd.read_file(geojson_file)

    # ajout du polygon sur la carte avec la couleur correspondant au niveau d'alerte (jaune ou rouge) avec bordure de la même couleur
    if filtered_df['severityLevel'].iloc[0] == 4:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'green', 'color': 'green'}).add_to(m)
    elif filtered_df['severityLevel'].iloc[0] == 3:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'yellow', 'color': 'yellow'}).add_to(m)
    elif filtered_df['severityLevel'].iloc[0] == 2:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'orange', 'color': 'orange'}).add_to(m)
    elif filtered_df['severityLevel'].iloc[0] == 1:
        folium.GeoJson(gdf, style_function=lambda x: {'fillColor': 'red', 'color': 'red'}).add_to(m)
    else:
        folium.GeoJson(gdf).add_to(m)


st.title('Carte Folium dans Streamlit')
folium_static(m)

col1, col2 = st.columns(2)

# Placez des éléments dans chaque colonne
with col1:
    st.header("Dataframe")
    st.dataframe(filtered_df)

with col2:
    st.header("Map")
    folium_static(m)