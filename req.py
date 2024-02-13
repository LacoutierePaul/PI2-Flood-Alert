import requests
import json
import pandas as pd

# clean the data from the stations
def clean_data_stations(df):
    # delete all the rows with a missing value in the columns 'lat' and 'long'
    df.dropna(subset=['lat', 'long'], inplace=True)

    # delete all the rows with a value in the columns 'lat' and 'long' in the form of a list
    df = df[~df['lat'].apply(lambda x: isinstance(x, list))]

    # verify that all stations have a unique 'stationReference'
    df = df.drop_duplicates(subset=['stationReference'])

    return df

# clean the data from the readings
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
def request_all_stations():
    url = 'http://environment.data.gov.uk/flood-monitoring/id/stations'

    try:
        api_request = requests.get(url)
        data = json.loads(api_request.content)
    except:
        data = None

    df = pd.DataFrame(data['items'])

    # keep only the columns 'lat', 'long', 'stationReference' and 'riverName'
    df = df[['lat', 'long', 'stationReference', 'riverName']]

    # clean the data
    df = clean_data_stations(df)

    return df

# request a particular station
def request_station(station):
    url = 'http://environment.data.gov.uk/flood-monitoring/id/stations'

    params = {
        'stationReference': station
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except:
        data = None

    df = pd.DataFrame(data['items'])

    # keep only the columns 'lat', 'long', 'stationReference' and 'riverName'
    df = df[['lat', 'long', 'stationReference', 'riverName']]

    # clean the data
    df = clean_data_stations(df)

    return df

# request a particular zone
def request_zone(latitude, longitude, radius):
    
    url = 'http://environment.data.gov.uk/flood-monitoring/id/stations'
    
    params = {
        'lat': latitude,
        'long': longitude,
        'dist': radius
    }
    
    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except:
        data = None
    
    df = pd.DataFrame(data['items'])

    # keep only the columns 'lat', 'long' and 'stationReference'
    df = df[['lat', 'long', 'stationReference']]

    # clean the data
    df = clean_data_stations(df)
    
    return df

# request all the readings
def request_all_readings(date):
    # format the date for the API parameters
    date = date.strftime('%Y-%m-%d')

    url = 'http://environment.data.gov.uk/flood-monitoring/data/readings'

    params = {
        'date': date,
        '_limit': 10000
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except:
        data = None

    df = pd.DataFrame(data['items'])

    # clean the data
    df = clean_data_readings(df)

    return df

# request a 'typicalRange' value
def request_typical_range(station):
    url = 'http://environment.data.gov.uk/flood-monitoring/id/stations/' + station + '/stageScale'

    try:
        api_request = requests.get(url)
        data = json.loads(api_request.content)
    except:
        data = None

    # search the 'typicalRangeHigh' and 'typicalRangeLow' values
    try:
        typical_range_high = data['items']['typicalRangeHigh']
    except:
        typical_range_high = None
    try:
        typical_range_low = data['items']['typicalRangeLow']
    except:
        typical_range_low = None
       
    return (typical_range_high,typical_range_low)
    
# merge two dataframes
def merge_dataframes(df_readings, df_stations, map=False):
    df = pd.merge(df_readings, df_stations, on='stationReference')

    # ensure that the lat and long columns are not null
    df.dropna(subset=['lat', 'long'], inplace=True)

    print(df.head())

    # drop the columns '@id', 'qualifier'
    df = df.drop(['@id', 'dateTime'], axis=1)

    if map:
        # place the columns
        df = df[['date', 'time', 'stationReference', 'lat', 'long', 'value', 'parameter', 'qualifier', 'period', 'unitName']]
    else:
        # place the columns
        df = df[['date', 'time', 'stationReference', 'lat', 'long', 'riverName', 'value', 'parameter', 'qualifier', 'period', 'unitName']]

    # sort by 'dateTime' in descending order
    df.sort_values(by=['date', 'time'], ascending=False, inplace=True)

    return df

# this function allows us to store every typical range high and low in a json file
def store_typical_range(df):
    stations = df['stationReference'].unique()

    typical_ranges = {}

    for station in stations:
        try:
            typical_range_high, typical_range_low = request_typical_range(station)
            typical_ranges[station] = {'typical_range_high': typical_range_high, 'typical_range_low': typical_range_low}
        except:
            typical_ranges[station] = {'typical_range_high': None, 'typical_range_low': None}

    with open('typical_range.json', 'w') as file:
        json.dump(typical_ranges, file, indent=4)

# function to calculate the number and percentage of staions without typical range
def calculate_percentage():
    try:
        with open('typical_range.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print('File not found.')
        return None
    
    count = 0
    for key in data:
        if data[key]['typical_range_high'] == None or data[key]['typical_range_low'] == None:
            count += 1
    
    total_count = len(data)
    percentage = (count / total_count) * 100

    return count, total_count, percentage