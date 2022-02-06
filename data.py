import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from geopy.geocoders import Nominatim 
import geocoder

data = requests.get('https://en.wikipedia.org/wiki/List_of_places_in_London').text

soup = BeautifulSoup(data, 'html.parser')

neighbourhoodList=[]

for row in soup.find('table').find_all('tr'):
    cells = row.find_all('td')
    if(len(cells) > 0):
        neighbourhoodList.append(cells[1].text)

df = pd.DataFrame({"Neighbourhood": neighbourhoodList})

def get_latlng(neighbourhood):
    lat_lng_coords = None
    g = geocoder.arcgis('{}, London, United Kingdom'.format(neighbourhood))
    lat_lng_coords = g.latlng
    return lat_lng_coords

coords = [ get_latlng(neighbourhood) for neighbourhood in df["Neighbourhood"].tolist() ]
df_coords = pd.DataFrame(coords, columns=['Latitude', 'Longitude'])
df['Latitude'] = df_coords['Latitude']
df['Longitude'] = df_coords['Longitude']
address = 'London, United Kingdom'
geolocator = Nominatim(user_agent="my-app")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude

radius = 2000
LIMIT = 50
venues = []

for lat, long, neighbourhood in zip(df['Latitude'], df['Longitude'], df['Neighbourhood']):
    url = "https://api.foursquare.com/v3/places/search?ll={},{}&radius={}&limit={}".format(
        lat,
        long,
        radius, 
        LIMIT)
    headers = {
    "Accept": "application/json",
    "Authorization": "fsq3HNLEhYNqCIjCmRx4OYjL4nj+HM1lCOZUHnhrC4AX7t0="
    }
    response = requests.request("GET", url, headers=headers).json()['results']

    for venue in response:
        name = venue ['name']
        latitude = venue ['geocodes']['main']['latitude']
        longitude = venue ['geocodes']['main']['longitude']
        category = venue['categories'][0]['name']
        venues.append((
            neighbourhood,
            lat, 
            long, 
            name, 
            latitude, 
            longitude,
            category
        ))

venues_df = pd.DataFrame(venues)
venues_df.to_csv('venues.csv')