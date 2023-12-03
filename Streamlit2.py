# to run the Streamlit web app type: streamlit run *.py

import requests
import streamlit as st
import json
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from folium import Circle
from folium import plugins

def create_map(latitude, longitude, our_radius):
    m = folium.Map(location=[latitude, longitude], zoom_start=6)

    # Add a marker for the selected point
    folium.Marker([latitude, longitude], popup="Point Sélectionné").add_to(m)

    # Add a circle around the selected point
    folium.Circle(
        location=[latitude, longitude],
        radius=our_radius * 1000,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.2,
        popup=f"Rayon du cercle: {our_radius} mètres"
    ).add_to(m)

    # Display the map in Streamlit
    url_stations = "http://environment.data.gov.uk/flood-monitoring/id/stations"

    params_stations2 = {
        'lat': latitude,
        'long': longitude,
        'dist': our_radius
    }

    try:
        api_request = requests.get(url_stations, params=params_stations2)
        data_stations = json.loads(api_request.content)
    except Exception as e:
        data_stations = "Error..."

    df2 = pd.DataFrame(data_stations['items'])
    df2 = df2[['lat', 'long', 'stationReference']]
    df2.dropna(subset=['lat', 'long'], inplace=True)
    # on supprime toutes les lignes avec des valeurs sous forme de liste dans les colonnes 'lat' et 'long'
    df2 = df2[~df2['lat'].apply(lambda x: isinstance(x, list))]

    marker_cluster = MarkerCluster().add_to(m)
    maliste=[]

    for index, row in df2.iterrows():
        folium.Marker([row['lat'], row['long']], popup=row['stationReference']).add_to(marker_cluster)
        maliste.append(row['stationReference'])

    folium_static(m)
    return maliste




st.write(""" # Pi² Diot-Siaci""")
date = st.date_input("Pick a date")
st.write("You picked : ", date)

# formattage de la date pour les paramètres de l'API
date_params = date.strftime("%Y-%m-%d")

url_readings = "http://environment.data.gov.uk/flood-monitoring/data/readings"
url_stations = "http://environment.data.gov.uk/flood-monitoring/id/stations"

params_readings = {
    #"latest": "true",
    #"today": "true",
    "date": date_params,
    #"since": "2023-01-01",
    "_limit": "10000",
}
params_stations = {
}
try:
    api_request = requests.get(url_readings, params=params_readings)
    data_readings = json.loads(api_request.content)
except Exception as e:
    data_readings = "Error..."
try:
    api_request = requests.get(url_stations, params=params_stations)
    data_stations = json.loads(api_request.content)
except Exception as e:
    data_stations = "Error..."

df = pd.DataFrame(data_readings['items'])
df_stations = pd.DataFrame(data_stations['items'])

# on ne garde que les colonnes 'lat', 'long' et 'stationReference'
df_stations = df_stations[['lat', 'long', 'stationReference']]

# ajout des colonnes 'parameter' et 'period' à partir de la colonne 'measure' (tout est dans l'URL) en utilisant regex
df[['stationReference', 'parameter', 'qualifier', 'period', 'unitName']] = df['measure'].str.extract(r'measures/(.*)-(.*)-(.*)-.-(.*)-(.*)')
# on supprime la colonne 'measure'
df = df.drop('measure', axis=1)

# on fusionne les deux dataframes
df = pd.merge(df, df_stations, on='stationReference')

# on supprime toutes les lignes avec une valeur manquante dans les colonnes 'lat' et 'long'
df.dropna(subset=['lat', 'long'], inplace=True)
# on supprime toutes les lignes avec des valeurs sous forme de liste dans les colonnes 'lat' et 'long'
df = df[~df['lat'].apply(lambda x: isinstance(x, list))]

# on supprime toutes les lignes avec comme paramètre autre que 'level'
df = df[df['parameter'] == 'level']

# trie par 'dateTime' dans l'ordre décroissant
df.sort_values(by=['dateTime'], ascending=False, inplace=True)

# on split la colonne 'dateTime' en deux colonnes 'date' et 'time'
df[['date', 'time']] = df['dateTime'].str.split('T', expand=True)
# affichage des alertes sur la dernière heure
df['dateTime'] = pd.to_datetime(df['dateTime'])
df['dateTime'] = df['dateTime'].dt.date

df_filtered = df[df['dateTime'] == date]

# on crée une carte centrée sur le Royaume-Uni
m = folium.Map(location=[51.5, -0.12], zoom_start=6)
# on ajoute les points
marker_cluster = MarkerCluster().add_to(m)
for index, row in df.iterrows():
    folium.Marker([row['lat'], row['long']], popup=row['stationReference']).add_to(marker_cluster)

# ajout des onglets
tabs = ["DataFrame", "Map", "Select by station","Find a station"]
selected_tab = st.sidebar.radio("Navigation", tabs)

if selected_tab == "DataFrame":
    # afficher le DataFrame dans le premier onglet
    st.header("DataFrame")
    st.write(date)
    st.dataframe(df_filtered)

elif selected_tab == "Map":
    # afficher la carte Folium dans le deuxième onglet
    st.header("Map")
    folium_static(m)

elif selected_tab == "Select by station":
    # possibilité de filtrer sur une station
    st.write( """## Filtrer sur une station""")
    cities=df['stationReference'].unique()
    choix_utilisateur = st.selectbox('Sélectionnez une station', cities)
    st.dataframe(df[df['stationReference']==choix_utilisateur])
    st.write("You picked : ", choix_utilisateur)
    import requests

    url = f"{url_stations}/{choix_utilisateur}"
    st.write(url)
    response = requests.get(url)
    data = response.json()
    try:
# Accéder à la clé "typicalRangeHigh" et "typicalRangeLow" dans la clé "stageScale"
        typical_range_high = data["items"]["stageScale"]["typicalRangeHigh"]
        typical_range_low = data["items"]["stageScale"]["typicalRangeLow"]
        st.write("Typical Range High:", typical_range_high)    
        st.write("Typical Range Low:", typical_range_low)
    except Exception as e :
        st.write("No typical range")

elif selected_tab=="Find a station":
    st.title("Sélection d'une Zone sur la Carte")

    # Two input fields for latitude and longitude
    latitude = st.number_input("Latitude:", value=51.5)
    longitude = st.number_input("Longitude:", value=-0.12)

    # Range slider for adjusting the radius of the circle
    our_radius = st.slider("Rayon du cercle (kilomètres):", min_value=1, max_value=100, value=50)

    # Load Map button
    if st.button("Load Map"):
        maliste= create_map(latitude, longitude, our_radius)
        st.dataframe(df[df['stationReference'].isin(maliste)])

