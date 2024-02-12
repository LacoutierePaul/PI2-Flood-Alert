import requests
import json
import pandas as pd

# request all the stations
def request_all_stations():
    url = "http://environment.data.gov.uk/flood-monitoring/id/stations"

    params = {
    }

    try:
        api_request = requests.get(url, params=params)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."

    df = pd.DataFrame(data['items'])

    # keep only the column 'stationReference'
    df = df['stationReference']

    # clean the data
    df = df.drop_duplicates()

    return df

# request a particular reading
def request_reading(station):
    url = "http://environment.data.gov.uk/flood-monitoring/data/readings"

    params = {
        "parameter": "level",
        "stationReference": station
    }

    try:
        api_request = requests.get(url, params=params)
        print(api_request.url)
        data = json.loads(api_request.content)
    except Exception as e:
        data = "Error..."

    df = pd.DataFrame(data['items'])

    return df

# now, we need to loop through all the stations and request the readings
stations = request_all_stations()

# define the variable to store the typical ranges
typical_ranges = {}

for station in stations:
    readings = request_reading(station)

    try:
        # calculate the typical range high (the measurement exceeded this for 5% of the relevant data)
        typical_range_high = readings['value'].quantile(0.95)

        # calculate the typical range low (the measurement exceeded this for 95% of the relevant data)
        typical_range_low = readings['value'].quantile(0.05)

        # store the typical ranges
        print(station, typical_range_high, typical_range_low)
        typical_ranges[station] = {'typical_range_high': typical_range_high, 'typical_range_low': typical_range_low}
    except:
        # store the typical ranges
        print(station, 'null', 'null')
        typical_ranges[station] = {'typical_range_high': None, 'typical_range_low': None}

# save the typical ranges to a file
with open('typical_ranges.json', 'w') as f:
    json.dump(typical_ranges, f)