import requests
import json
import pandas as pd
url = 'https://environment.data.gov.uk/flood-monitoring/data/readings.csv'
params = {
    'date': '2023-01-01',
}
df = pd.read_csv(url, parse_dates=['dateTime'])

df.head(10)

