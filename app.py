# to run the Streamlit web app type: streamlit run *.py

# imports
import req

import pandas as pd

import streamlit as st

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static



def create_map_risks(latitude, longitude, our_radius):
    m = folium.Map(location=[latitude, longitude], zoom_start=6)

    # add a marker for the selected point
    folium.Marker([latitude, longitude], popup="Selected point").add_to(m)

    # add a circle around the selected point
    folium.Circle(
        location=[latitude, longitude],
        radius=our_radius * 1000,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.2,
        popup=f"Rayon du cercle: {our_radius} mètres"
    ).add_to(m)

    # request
    df_zone = req.request_zone(latitude, longitude, our_radius)

    # merge the two dataframes
    df = req.merge_dataframes(df_readings, df_zone)

    marker_cluster = MarkerCluster().add_to(m)
    rows=[]

    for index, row in df.iterrows():
        folium.Marker([row['lat'], row['long']], popup=warning(df, req.request_typical_range(row['stationReference'], risk=True), map=True)).add_to(marker_cluster)
        rows.append(req.request_typical_range(row['stationReference']))

    folium_static(m)
    return rows

def warning(df, typical_range_high, map=False):
    if typical_range_high != None:
        if df['value'].max() > typical_range_high:
            return("Warning! (" + str(typical_range_high) + ")") if map else ("Warning!")
        else:
            return("No warning. (" + str(typical_range_high) + ")") if map else ("No warning.")
    else:
        return("No data.")

st.write("""# Pi² Diot-Siaci""")
date = st.date_input("Pick a date")
st.write("You picked: ", date)

# requests
df_readings = req.request_all_readings(date)
df_stations = req.request_all_station()

# merge the two dataframes
df = req.merge_dataframes(df_readings, df_stations)

# add the tabbed layout
tabs = ["Dataframe", "Map","Current Warnings", "Select a station", "Find a station"]
selected_tab = st.sidebar.radio("Navigation", tabs)

if selected_tab == "Dataframe":
    st.header("Dataframe")

    st.write(date)

    df['dateTime'] = pd.to_datetime(df['dateTime'])
    df['dateTime'] = df['dateTime'].dt.date

    st.dataframe(df[df['dateTime'] == date])

elif selected_tab == "Map":
    st.header("Map")

    # create a map centered on the UK
    m = folium.Map(location=[51.5, -0.12], zoom_start=6)

    # add clusters of markers
    marker_cluster = MarkerCluster().add_to(m)
    for index, row in df.iterrows():
        folium.Marker([row['lat'], row['long']], popup=row['stationReference']).add_to(marker_cluster)  
    
    # show the map
    folium_static(m)

elif selected_tab == "Select a station":
    st.header( "Sort on a particular station")

    # ensure that the stationReference column is unique
    cities = df['stationReference'].unique()
    
    # choice from the user
    choice = st.selectbox('Select a station', cities)

    # filter the dataframe
    df_station = df[df['stationReference']==choice]
    st.dataframe(df_station)
    st.write("You picked: ", choice)

    typical_range_high, typical_range_low = req.request_typical_range(choice)

    st.write("Typical range high: ", typical_range_high)
    st.write("Typical range low: ", typical_range_low)

    # warning
    st.write(warning(df_station, typical_range_high))

elif selected_tab=="Find a station":
    st.title("Select a zone on the map")

    # two input fields for latitude and longitude
    latitude = st.number_input("Latitude:", value=51.5)
    longitude = st.number_input("Longitude:", value=-0.12)

    # range slider for adjusting the radius of the circle
    our_radius = st.slider("Radius (kilometers):", min_value=1, max_value=100, value=50)

    # load Map button
    if st.button("Load map"):
        maliste= create_map_risks(latitude, longitude, our_radius)
        st.dataframe(df[df['stationReference'].isin(maliste)])

elif selected_tab=="Current Warnings":
    st.title("All the current warnings in England: ")
    
    stations=df["stationReference"].unique()
    
    warnings=[]
    for s in stations:
        typicalRange=req.request_typical_range(s,risk=True)
        row=df[df['stationReference']==s]

        if typicalRange!=None:
            if row['value'].max()>typicalRange:
                st.write("Warning in the station: ",s)
                warnings.append(s)