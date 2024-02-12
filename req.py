import requests
import json
import pandas as pd

def clean_data_stations(df):
    # delete all the rows with a missing value in the columns 'lat' and 'long'
    df.dropna(subset=['lat', 'long'], inplace=True)

    # delete all the rows with a value in the columns 'lat' and 'long' in the form of a list
    df = df[~df['lat'].apply(lambda x: isinstance(x, list))]

    # verify that all stations have a unique 'stationReference'
    df = df.drop_duplicates(subset=['stationReference'])

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
def request_typical_range(station):
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
       
    return (typical_range_high,typical_range_low)
    
# merge two dataframes
def merge_dataframes(df_readings, df_stations):
    df = pd.merge(df_readings, df_stations, on='stationReference')

    # ensure that the lat and long columns are not null
    df.dropna(subset=['lat', 'long'], inplace=True)

    # sort by 'dateTime' in descending order
    df.sort_values(by=['dateTime'], ascending=False, inplace=True)

    return df

# this function allows us to store every typical range high and low in a json file
def store_typical_range(df):
    stations=df['stationReference'].unique()

    typical_range_dict={}

    for s in stations:
        try:
            typicalRH,typicalRL=request_typical_range(s)
            typical_range_dict[s]={"typical_range_high":typicalRH,"typical_range_low":typicalRL}
        except Exception as e:
            print(e)

    with open('typical_range.json','w') as file:
        json.dump(typical_range_dict, file, indent=4)

# function to calculate the number and percentage of staions without typical range
def calculate_percentage():
    file = open('typical_range.json')
    data = json.load(file)
    
    count = 0
    for key in data:
        if data[key]['typical_range_high'] == None or data[key]['typical_range_low'] == None:
            count += 1
    
    total_count = len(data)
    percentage = (count / total_count) * 100

    return count, total_count, percentage

def calculate_risk_percentage():
    try:
        with open('typical_range.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Le fichier 'typical_range.json' n'a pas été trouvé.")
        return None
    risk_count = 0
    for key in data:
        if data[key]['typical_range_high'] is None or data[key]['typical_range_low'] is None:
            risk_count += 1
    total_stations = len(data)
    risk_percentage = (risk_count / total_stations) * 100

    return risk_count, total_stations, risk_percentage

def identify_high_risk_stations(df_readings):
    try:
        with open('typical_range.json', 'r') as file:
            typical_range_data = json.load(file)
    except FileNotFoundError:
        print("Le fichier 'typical_range.json' n'a pas été trouvé.")
        return None
    df_merged = pd.merge(df_readings, pd.DataFrame(typical_range_data).T,
                         left_on='stationReference', right_index=True)
    high_risk_stations = df_merged[df_merged['value'] > df_merged['typical_range_high']]

    return high_risk_stations