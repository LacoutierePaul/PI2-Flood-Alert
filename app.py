# to run the Streamlit web app type: streamlit run *.py

# imports
import req

from math import radians, cos, sin, sqrt, atan2
import time

import pandas as pd

import streamlit as st

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

class SessionState:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

@st.cache(allow_output_mutation=True)
def get_state():
    return SessionState(points=[])

state = get_state()

def distance_calculation(lat1, lon1, lat2, lon2):
    # convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # haversine formula to calculate distance between two points on a sphere
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_of_earth = 6371 # radius of Earth in kilometers

    distance = radius_of_earth * c

    return distance

def warning(df, typical_range):
    typical_range_high, typical_range_low = typical_range
    
    if typical_range_high != None:
        if df['value'].max() > typical_range_high:
            return("Warning!")
        else:
            return("No warning")
    else:
        return("No data")

def create_map_risks(points):
    m = folium.Map(location=[points[0][2], points[0][3]], zoom_start=6)

    # create a dataframe with the columns 'pointName', 'insuredValue', 'stationReference', 'pointDistance', 'exceedancePercentage', 'warning'
    summary_df = pd.DataFrame(columns=['pointName', 'insuredValue', 'stationReference', 'pointDistance', 'exceedancePercentage', 'warning'])

    marker_cluster = MarkerCluster().add_to(m)
    rows = []

    for point in points:
        name, insured_value, latitude, longitude, our_radius = point

        # add a marker for the selected point
        folium.Marker([latitude, longitude], popup=name).add_to(marker_cluster)

        # add a circle around the selected point 
        folium.Circle(location=[latitude, longitude], radius=our_radius*1000, color='transparent', fill=False, popup=f"Rayon du cercle: {our_radius} mètres").add_to(m)

        # request
        df_zone = req.request_zone(latitude, longitude, our_radius)

        # merge the two dataframes
        required_columns = ['lat', 'long', 'stationReference']
        if all(column in df_zone.columns for column in required_columns):
            # merge the two dataframes
            df = req.merge_dataframes(df_readings, df_zone)

            for index, row in df.iterrows():
                warning_message = warning(df, req.request_typical_range(row['stationReference'], risk=True))
                popup_color = "red" if warning_message == "Warning!" else "green" if warning_message == "No warning." else "gray"

                folium.Marker(
                    [row['lat'], row['long']],
                    popup=folium.Popup(warning_message, parse_html=True),
                    icon=folium.Icon(color=popup_color)
                ).add_to(marker_cluster)

                rows.append(req.request_typical_range(row['stationReference']))

                # compute the percentage of exceedance between the value and the typical range
                typical_range_high = req.request_typical_range(row['stationReference'])[0]
                if typical_range_high != None:
                    exceedance_percentage = round((row['value'] - typical_range_high) / typical_range_high * 100, 2)
                else:
                    exceedance_percentage = 'No data'

                # append information to summary_df
                new_row = {
                    'pointName': name,
                    'insuredValue': insured_value,
                    'stationReference': row['stationReference'],
                    'pointDistance': distance_calculation(latitude, longitude, row['lat'], row['long']),
                    'exceedancePercentage': exceedance_percentage,
                    'warning': warning_message
                }

                summary_df = pd.concat([summary_df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            st.warning("The required columns are not present in the dataframe.")

    folium_static(m)
    return rows, summary_df

st.write("""# Pi² Diot-Siaci""")
date = st.date_input("Pick a date")
st.write("You picked: ", date)

# requests
df_readings = req.request_all_readings(date)
df_stations = req.request_all_station()

# merge the two dataframes
df = req.merge_dataframes(df_readings, df_stations)

# retrieve the typical ranges stored in a json file for every station
try:
    file_path  ='typical_range.json'
    typical_ranges = pd.read_json(file_path,orient='index')
    typical_ranges.reset_index(inplace=True)
    typical_ranges.rename(columns={'index': 'Station'}, inplace=True)
except Exception as e:
    print(e)

# add the tabbed layout
tabs = ["Dataframe", "Map", "Select a station", "Find a station", "Current warnings"]
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
    points=[]

    # two input fields for latitude and longitude
    name = st.text_input("Name of the point:", value="First point")
    insured_value = st.number_input("Insured value:", value=1000000)
    latitude = st.number_input("Latitude:", value=51.5)
    longitude = st.number_input("Longitude:", value=-0.12)

    # range slider for adjusting the radius of the circle
    our_radius = st.slider("Radius (kilometers):", min_value=1, max_value=20, value=5)
    if st.button("Add point"):
        # check that there is no point with the same name
        if any(point[0] == name for point in state.points):
            st.warning(f"The point '{name}' already exists.")
        else:
            state.points.append([name, insured_value, latitude, longitude, our_radius])

    uploaded_file = st.file_uploader("Choose a file", type="csv")
    if st.button("Add points from a csv file"):
        if uploaded_file is not None:
            try:
                df_points = pd.read_csv(uploaded_file)
                print(df_points)

                st.write("List of points to add:")
                st.dataframe(df_points)

                for index, row in df_points.iterrows():
                    # check that there is no point with the same name
                    if any(point[0] == row['name'] for point in state.points):
                        st.warning(f"The point '{row['name']}' already exists.")
                    else:
                        state.points.append([row['name'], row['insured_value'], row['latitude'], row['longitude'], row['radius']])
            except Exception as e:
                st.error(f"Error: {e}")
    
    if st.button("Clear point(s)"):
        state.points = []

    if state.points:
        st.write("List of Points:", state.points)

    # load map button
    if st.button("Load map"):
        if state.points:
            print("Loading the map...")
            rows, summary_df = create_map_risks(state.points)
            print("Completed !")

            # display the summary dataframe by warning first, then by insured value and finally by distance
            st.dataframe(summary_df.sort_values(by=['warning', 'pointDistance', 'insuredValue']))

            state.points = []
        else:
            st.warning("Please add at least one point before loading the map.")

elif selected_tab=="Current warnings":
    st.title("All the current warnings in England: ")

    # some staistics about the typical ranges
    st.write("Typical ranges statistics: ")

    count, total_count, percentage = req.calculate_percentage()

    st.write("Number of stations without typical range: ", count)
    st.write("Total number of stations: ", total_count)
    st.write("Percentage: ", percentage)
    
    stations = df["stationReference"].unique()
    
    warnings=[]
    for s in stations:
        try:
            typical_range_high = typical_ranges.loc[typical_ranges['Station'] == s, "typical_range_high"].iloc[0]
            row = df[df['stationReference']==s]

            if typical_range_high != None:
                if row['value'].max() > typical_range_high:
                    warnings.append([s, typical_range_high, row['value'].max()])
                    
        except Exception as e:
            print(e)
        
    warnings_df = pd.DataFrame(warnings, columns=["Station with warning", "Typical range high", "Current value"])
    st.dataframe(warnings_df)