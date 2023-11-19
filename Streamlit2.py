#Code
# To run the Streamlit web app type: python -m streamlit run Streamlit.py or streamlit run Streamlite.py


import requests
import streamlit as st
from streamlit_folium import folium_static
import json
import pandas as pd
import folium
import geopandas as gpd

# ...

st.write(""" # Pi² Diot-Siaci""")
date = st.date_input("Pick a date")
st.write("You pick : ", date)

url = "http://environment.data.gov.uk/flood-monitoring/id/floods"
params = {
    #'date': date,
    "min-severity": 3
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
# affichage des alertes sur la dernière heure
df['timeRaised'] = pd.to_datetime(df['timeRaised'])
df['timeRaised'] = df['timeRaised'].dt.date
#st.dataframe(df)

filtered_df = df[df['timeRaised'] == date]

# Créer une carte Folium ou tout autre élément de votre application Streamlit
# Afficher le DataFrame filtré dans votre application
st.title(f'Données pour la date {date}')
filtered_df = filtered_df.sort_values(by='severityLevel')

# Définissez le style en fonction du niveau de gravité à l'extérieur de la boucle
def get_style(severity_level):
    if severity_level == 4:
        return {'fillColor': 'green', 'color': 'green'}
    elif severity_level == 3:
        return {'fillColor': 'yellow', 'color': 'yellow'}
    elif severity_level == 2:
        return {'fillColor': 'orange', 'color': 'orange'}
    elif severity_level == 1:
        return {'fillColor': 'red', 'color': 'red'}

# Créez la carte une seule fois
m = folium.Map(location=[53.5, -1.5], zoom_start=6)

# Utilisez iterrows pour itérer sur les lignes du DataFrame
for index, row in filtered_df.head(10).iterrows():
    geojson_file = row['floodArea']
    
    # Ajoutez le polygon avec le style correspondant
    folium.GeoJson(gpd.read_file(geojson_file), style_function=lambda x: get_style(row['severityLevel'])).add_to(m)
   
# Ajoutez des onglets
tabs = ["Dataframe", "Map","Select by City"]
selected_tab = st.sidebar.radio("Navigation", tabs)

if selected_tab == "Dataframe":
    # Affichez le DataFrame dans le premier onglet
    st.header("Dataframe")
    st.dataframe(filtered_df)

elif selected_tab == "Map":
    # Affichez la carte Folium dans le deuxième onglet
    st.header("Map")
    folium_static(m)

elif selected_tab == "Select by City":
    # Possibilité de filtrer sur une ville le df
    st.write( """## Filtrer sur une ville""")
    cities=df['eaAreaName'].unique()
    choix_utilisateur = st.selectbox('Sélectionnez une ville', cities)
    st.dataframe(df[df['eaAreaName']==choix_utilisateur])
