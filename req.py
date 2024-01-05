import requests
import json
import pandas as pd

def clean_data_stations(df):
    # delete all the rows with a missing value in the columns 'lat' and 'long'
    df.dropna(subset=['lat', 'long'], inplace=True)

    # delete all the rows with a value in the columns 'lat' and 'long' in the form of a list
    df = df[~df['lat'].apply(lambda x: isinstance(x, list))]

    return df

def clean_data_readings(df):
    # add columns 'stationReference', 'parameter', 'qualifier', 'period' and 'unitName' from the column 'measure' (everything is in the URL) with regex
    df[['stationReference', 'parameter', 'qualifier', 'period', 'unitName']] = df['measure'].str.extract(r'measures/(.*)-(.*)-(.*)-.-(.*)-(.*)')
    # drop the column 'measure'
    df = df.drop('measure', axis=1)

    # on supprime toutes les lignes avec comme paramètre autre que 'level'
    df = df[df['parameter'] == 'level']

    # split the column 'dateTime' into two columns 'date' and 'time'
    df[['date', 'time']] = df['dateTime'].str.split('T', expand=True)

    return df

# request all the stations
def request_all_station():
    url = "http://environment.data.gov.uk/flood-monitoring/id/stations"

    params = {
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."

    df = pd.DataFrame(data['items'])

    # keep only the columns 'lat', 'long' and 'stationReference'
    df = df[['lat', 'long', 'stationReference']]

    # clean the data
    df = clean_data_stations(df)

    return df

# request a particular station
def request_station(station):
    url = "http://environment.data.gov.uk/flood-monitoring/id/stations"

    params = {
        "stationReference": station
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."

    df = pd.DataFrame(data['items'])

    # keep only the columns 'lat', 'long' and 'stationReference'
    df = df[['lat', 'long', 'stationReference']]

    # clean the data
    df = clean_data_stations(df)

    return df

def request_zone(latitude, longitude, radius):
    
    url = "http://environment.data.gov.uk/flood-monitoring/id/stations"
    
    params = {
        'lat': latitude,
        'long': longitude,
        'dist': radius
    }
    
    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."
    
    df = pd.DataFrame(data['items'])

    # keep only the columns 'lat', 'long' and 'stationReference'
    df = df[['lat', 'long', 'stationReference']]

    # clean the data
    df = clean_data_stations(df)
    
    return df

# request all the readings
def request_all_readings(date):
    # format the date for the API parameters
    date = date.strftime("%Y-%m-%d")

    url = "http://environment.data.gov.uk/flood-monitoring/data/readings"

    params = {
        "date": date,
        "_limit": "10000",
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."

    df = pd.DataFrame(data['items'])

    # clean the data
    df = clean_data_readings(df)

    return df

# request a 'typicalRange' value
def request_typical_range(station, risk=False):
    url = "http://environment.data.gov.uk/flood-monitoring/id/stations/" + station + "/stageScale"

    params = {
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."

    # search the 'typicalRangeHigh' and 'typicalRangeLow' values
    try:
        typical_range_high = data["items"]["typicalRangeHigh"]
    except Exception as e:
        typical_range_high = None
    try:
        typical_range_low = data["items"]["typicalRangeLow"]
    except Exception as e:
        typical_range_low = None

    if risk:
        return typical_range_high
    else:
        return typical_range_high, typical_range_low
    
# merge two dataframes
def merge_dataframes(df_readings, df_stations):
    df = pd.merge(df_readings, df_stations, on='stationReference')

    # ensure that the lat and long columns are not null
    df.dropna(subset=['lat', 'long'], inplace=True)

    # sort by 'dateTime' in descending order
    df.sort_values(by=['dateTime'], ascending=False, inplace=True)

    return df
