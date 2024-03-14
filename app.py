# to run the Streamlit web app type: streamlit run *.py

# imports
import req
from math import radians, cos, sin, sqrt, atan2
import numpy as np
from datetime import datetime
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

st.title('Pi² Diot-Siaci (team 213)')
max_date = datetime.now().date()
date = st.date_input('Pick a date', max_value=max_date)
st.write('You picked:', date)

@st.cache_data
def request_data(chosen_date):
    # requests
    df_readings = req.request_all_readings(chosen_date)
    df_stations = req.request_all_stations()

    # merge the two dataframes
    df = req.merge_dataframes(df_readings, df_stations)

    # retrieve the typical ranges stored in a json file for every station
    try:
        file_path = 'typical_ranges.json'
        typical_ranges = pd.read_json(file_path, orient='index')
        typical_ranges.reset_index(inplace=True)
        typical_ranges.rename(columns={'index': 'stationReference'}, inplace=True)
    except Exception as e:
        print(e)

    return df, df_readings, df_stations, typical_ranges

df, df_readings, df_stations, typical_ranges = request_data(date)

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

def warning(exceedance_percentage):
    if exceedance_percentage is not None:
        if exceedance_percentage > 0:
            return("Warning!")
        else:
            return("No warning")
    else:
        return("No data")

def create_map_risks(points):
    m = folium.Map(location=[points[0][2], points[0][3]], zoom_start=6)

    # create a dataframe with the columns 'pointName', 'insuredValue', 'stationReference', 'pointDistance', 'exceedancePercentage', 'warning'
    summary_df = pd.DataFrame(columns=['pointName', 'insuredValue', 'stationReference', 'pointDistance', 'exceedancePercentage', 'warning'])

    marker_cluster = MarkerCluster(disable_clustering_at_zoom=1).add_to(m)
    rows = []

    for point in points:
        name, insured_value, latitude, longitude, our_radius = point

        # add a marker for the selected point
        folium.Marker([latitude, longitude], popup=name).add_to(marker_cluster)

        # add a circle around the selected point 
        folium.Circle(location=[latitude, longitude], radius=our_radius*1000, color='transparent', fill=False, popup=f"Rayon du cercle: {our_radius} mètres").add_to(m)

        # requests
        df_latest_readings = req.request_latest_readings()
        df_zone = req.request_zone(latitude, longitude, our_radius)

        # merge the two dataframes
        required_columns = ['lat', 'long', 'stationReference']
        if all(column in df_zone.columns for column in required_columns):
            # merge the two dataframes
            df = req.merge_dataframes(df_latest_readings, df_zone, True)

            for index, row in df.iterrows():
                station = row['stationReference']

                typical_range_high = typical_ranges[typical_ranges['stationReference'] == station]['typical_range_high'].iloc[0]

                # compute the percentage of exceedance between the value and the typical range high
                print(typical_range_high)
                if typical_range_high is not None and not np.isnan(typical_range_high):
                    if row['value'] > typical_range_high:
                        exceedance_percentage = round((row['value'] - typical_range_high) / typical_range_high * 100, 2)
                    else:
                        exceedance_percentage = 0
                else:
                    exceedance_percentage = 'No data'

                warning_message = warning(exceedance_percentage)
                popup_color = "red" if warning_message == "Warning!" else "green" if warning_message == "No warning" else "gray"

                folium.Marker(
                    [row['lat'], row['long']],
                    popup=folium.Popup(warning_message, parse_html=True),
                    icon=folium.Icon(color=popup_color)
                ).add_to(marker_cluster)

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

# add the tabbed layout
tabs = ['Home','All the readings', 'Map of all the stations', 'Find a station', 'Make your own map', 'Current warnings']
selected_tab = st.sidebar.radio('Navigation', tabs)

if selected_tab == 'Home': 
    st.header("Home")
    st.write ("Bienvenue sur le site web de notre projet d'alerting innondation.")
    st.write("Ce projet utilise les données du gouvernement britannique qui sont disponnible sur ce lien : ")
    st.image("https://upload.wikimedia.org/wikipedia/fr/thumb/4/4b/HM_Government_logo.svg/1200px-HM_Government_logo.svg.png", use_column_width=True, width=20)

    st.markdown("#### Page All the readings : ")
    st.write("Cette page affiche un tableau contenant toutes les lectures de mesure en Grande-Bretagne. Il est possible de trier le tableau en cliquant sur les en-têtes de colonne.")

    st.text("")

    st.markdown("#### Page Map of all the stations : ")
    st.write("Cette page affiche une carte avec tous les stations de mesure en Grande-Bretagne. Il est possible de cliquer sur les marqueurs pour voir la référence de la station.")

    st.text("")

    st.markdown("#### Page Find a station :")
    st.write('Sur cette page, vous pouvez sélectionner une zone sur la carte en spécifiant la latitude, la longitude et le rayon du cercle. Lorsque vous appuyez sur le bouton "Load Map", la carte affiche les stations de mesure qui se trouvent dans la zone spécifiée. Les données correspondantes à cette station sont aussi disponnibles.')

    st.markdown("#### Page Make your own map : ")
    st.write("Cette page permet de créer une carte personnalisée en Grande-Bretagne. Il est possible d'ajouter des points en spécifiant un nom, une valeur assurée, une latitude, une longitude et un rayon. Les points peuvent également être ajoutés à partir d'un fichier CSV. Une fois que les points sont ajoutés, la carte peut être chargée, ce qui affiche un résumé des risques pour chaque point.")

    st.markdown("#### Page Current warnings : ")
    st.write("Cette page affiche les avertissements actuels en Grande-Bretagne. Elle affiche d'abord des statistiques sur les plages typiques, puis les avertissements pour chaque station.")



elif selected_tab == 'All the readings':
    st.header('All the readings in Great Britain')

    st.write('The table below shows all the readings in Great Britain.')
    st.write('You can sort the table by clicking on the column headers.')

    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].dt.date

    st.dataframe(df[df['date'] == date])

elif selected_tab == 'Map of all the stations':
    st.header('Map of all the stations in Great Britain')

    st.write('The map below shows all the stations in Great Britain.')
    st.write('You can click on the markers to see the stationReference.')
    st.write('Here is the number of stations:', len(df_stations))

    # create a map centered on the UK
    m = folium.Map(location=[51.5, -0.12], zoom_start=6)

    # add clusters of markers
    marker_cluster = MarkerCluster().add_to(m)
    for index, row in df_stations.iterrows():
        folium.Marker([row['lat'], row['long']], popup=row['stationReference']).add_to(marker_cluster)  
    
    # show the map
    folium_static(m)

elif selected_tab == 'Find a station':
    st.header('Find a station in Great Britain')

    st.write('The table below shows the readings for a particular station.')
    st.write('You can sort the table by clicking on the column headers.')

    # ensure that the stationReference column is unique
    cities = df['stationReference'].unique()
    
    # choice from the user
    choice = st.selectbox('Select a station', cities)

    # filter the dataframe
    df_station = df[df['stationReference'] == choice]
    st.dataframe(df_station)

    st.write('Here is some other information about the station:')

    typical_range = typical_ranges.loc[typical_ranges['stationReference'] == choice, ['typical_range_high', 'typical_range_low']].iloc[0]

    st.write('Typical range high:', typical_range[0])
    st.write('Typical range low:', typical_range[1])

    exceedance_percentage = None
    if typical_range[0] is not None and not np.isnan(typical_range[0]):
        exceedance_percentage = round((df_station['value'].max() - typical_range[0]) / typical_range[0] * 100, 2)

    # display the warning
    st.write(warning(exceedance_percentage))

elif selected_tab=='Make your own map':
    st.header('Make your own map in Great Britain')
    points=[]

    # input fields for the user (pre-filled with default values)
    name = st.text_input('Name of the point:', value='First point')
    insured_value = st.number_input('Insured value:', value=0)
    latitude = st.number_input('Latitude:', value=51.5)
    longitude = st.number_input('Longitude:', value=-0.12)
    radius = st.slider('Radius (in kilometers):', min_value=1, max_value=20, value=5)

    # add point button
    if st.button('Add point'):
        # check that there is no point with the same name
        if any(point[0] == name for point in state.points):
            st.warning(f"The point '{name}' already exists.")
        else:
            state.points.append([name, insured_value, latitude, longitude, radius])

    # add point(s) from a csv file button
    uploaded_file = st.file_uploader('Choose a file', type='csv')
    if st.button('Add point(s) from a csv file'):
        if uploaded_file is not None:
            try:
                df_points = pd.read_csv(uploaded_file)

                for index, row in df_points.iterrows():
                    # check that there is no point with the same name
                    if any(point[0] == row['name'] for point in state.points):
                        st.warning(f"The point '{row['name']}' already exists.")
                    else:
                        state.points.append([row['name'], row['insured_value'], row['latitude'], row['longitude'], row['radius']])
            except Exception as e:
                st.error(f'Error: {e}')
    
    # clear point(s) button
    if st.button('Clear point(s)'):
        state.points = []

    # display your point(s)
    if state.points:
        st.write('Your point(s):')
        df_points = pd.DataFrame(state.points, columns=['Name', 'Insured value', 'Latitude', 'Longitude', 'Radius'])
        st.dataframe(df_points)

    # load map button
    if st.button('Load map'):
        if state.points:
            # create the map
            rows, summary_df = create_map_risks(state.points)

            # display the summary dataframe by warning first, then by insured value and finally by distance
            st.dataframe(summary_df.sort_values(by=['warning', 'pointDistance', 'insuredValue']))

            # reset the points
            state.points = []
        else:
            st.warning('Please add at least one point before loading the map.')

elif selected_tab=='Current warnings':
    st.header('Current warnings in Great Britain')

    st.write('The table below shows the current warnings in Great Britain.')
    st.write('You can first see some statistics about the typical ranges and then the warnings for each station.')

    # calculate the percentage of stations without typical range
    count, total_count, percentage = req.calculate_percentage()

    st.write('Number of stations without typical range:', count)
    st.write('Total number of stations:', total_count)
    st.write('Percentage:', percentage)
    
    warnings = []
    for s in df_stations['stationReference']:
        try:
            typical_range_high = typical_ranges[typical_ranges['stationReference'] == s]['typical_range_high'].iloc[0]
            row = df[df['stationReference']==s]

            if typical_range_high is not None and not np.isnan(typical_range_high):
                if row['value'].max() > typical_range_high:
                    warnings.append([s, typical_range_high, row['value'].max()])
        except Exception as e:
            print(e)
        
    warnings_df = pd.DataFrame(warnings, columns=['Station(s) with warning', 'Typical range high', 'Current value'])
    st.dataframe(warnings_df)