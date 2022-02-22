import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from geopy.geocoders import Nominatim
import geocoder
import folium
from streamlit_folium import folium_static
from sklearn.cluster import KMeans


st.title("Neighbourhood Explorer")
st.sidebar.title("London Edition")

data = requests.get('https://en.wikipedia.org/wiki/List_of_places_in_London').text

soup = BeautifulSoup(data, 'html.parser')

neighbourhoodList=[]

for row in soup.find('table').find_all('tr'):
    cells = row.find_all('td')
    if(len(cells) > 0):
        neighbourhoodList.append(cells[1].text)

df = pd.DataFrame({"Neighbourhood": neighbourhoodList})

@st.cache(persist = True)
def get_latlng(neighbourhood):
    lat_lng_coords = None
    g = geocoder.arcgis('{}, London, United Kingdom'.format(neighbourhood))
    lat_lng_coords = g.latlng
    return lat_lng_coords

coords = [ get_latlng(neighbourhood) for neighbourhood in df["Neighbourhood"].tolist() ]
df_coords = pd.DataFrame.from_records(coords, columns=['Latitude', 'Longitude'])
df['Latitude'] = df_coords['Latitude']
df['Longitude'] = df_coords['Longitude']
address = 'London, United Kingdom'
geolocator = Nominatim(user_agent="my-app")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
st.sidebar.markdown('The geographical coordinates of London are {}, {}.'.format(latitude, longitude))

venues = pd.read_csv("venues.csv")

uniquevenues = venues['VenueCategory'].unique()
venues_list = []
for uniquevenue in uniquevenues:
    venues_list.append(uniquevenue)

choice = st.sidebar.selectbox("What would you like to do?", options = ["Explore a Venue", "Explore a Neighbourhood"])
venues_onehot = pd.get_dummies(venues[['VenueCategory']], prefix="", prefix_sep="")
venues_onehot['Neighbourhood'] = venues['Neighbourhood'] 
fixed_columns = [venues_onehot.columns[-1]] + list(venues_onehot.columns[:-1])
venues_onehot = venues_onehot[fixed_columns]
neighbourhoods = list (venues_onehot['Neighbourhood'].unique())

if choice == "Explore a Neighbourhood":
    neighbourhood = st.sidebar.selectbox("Choose a Neighbourhood", options = neighbourhoods)
    venues_filtered = venues[venues['Neighbourhood']==neighbourhood]

    coords = df[df['Neighbourhood']==neighbourhood]
    latitude = coords['Latitude'].iloc[0]
    longitude = coords['Longitude'].iloc[0]

    map_clusters = folium.Map(location=[latitude, longitude], zoom_start=13)

    venues_grouped = venues_filtered.groupby(['VenueCategory']).size().reset_index(name="count")
    pop_venues_grouped = venues_grouped.sort_values(['count'], ascending = False)
    least_pop_venues_grouped = venues_grouped.sort_values(['count'])
    pop_cats = str(list(pop_venues_grouped['VenueCategory'])[0:5])[1:-1]
    least_pop_cats = str(list(least_pop_venues_grouped['VenueCategory'])[0:5])[1:-1]
    st.sidebar.write("The Most Common Venues in this Neighbourhood are:")
    st.sidebar.write(pop_cats)
    st.sidebar.write("The Least Common Venues in this Neighbourhood are:")
    st.sidebar.write(least_pop_cats)

    if st.sidebar.checkbox("Show Me A Specific Venue", False):
            venue =  st.sidebar.selectbox("Choose a Venue", options = uniquevenues)
            venues_filtered = venues_filtered[venues_filtered['VenueCategory']== venue]
        
    for lat, lon, cat, name in zip(venues_filtered['VenueLatitude'], venues_filtered['VenueLongitude'], venues_filtered['VenueCategory'], venues_filtered['VenueName']):
        label = folium.Popup(str(name) + ' Category: ' + str(cat), parse_html=True)
        folium.CircleMarker(
            [lat, lon],
            radius=5,
            popup=label,
            color='blue',
            fill=True,
            fill_color="##3186cc",
            fill_opacity=0.7).add_to(map_clusters)

    folium_static (map_clusters)

elif choice == "Explore a Venue":
    venue = st.sidebar.selectbox("Choose a Venue", options = uniquevenues)
    venues_filtered = venues[venues['VenueCategory']==venue]

    venues_grouped = venues_filtered.groupby(['Neighbourhood']).size().reset_index(name="count")
    pop_n_grouped = venues_grouped.sort_values(['count'], ascending = False)
    least_pop_n_grouped = venues_grouped.sort_values(['count'])
    pop_cats = str(list(pop_n_grouped['Neighbourhood'])[0:5])[1:-1]
    least_pop_cats = str(list(least_pop_n_grouped['Neighbourhood'])[0:5])[1:-1]
    st.sidebar.write("The Most Popular Neighbourhoods for this Venue are:")
    st.sidebar.write(pop_cats)
    st.sidebar.write("The Least Popular Neighbourhoods for this Venue are:")
    st.sidebar.write(least_pop_cats)

    specific = st.sidebar.checkbox("Show Me A Specific Neighbourhood", False)
    if specific:
        neighbourhood =  st.sidebar.selectbox("Choose a Neighbourhood", options = neighbourhoods)
        venues_filtered = venues_filtered[venues_filtered['Neighbourhood']== neighbourhood]

    map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)
        
    for lat, lon, neigh, name in zip(venues_filtered['VenueLatitude'], venues_filtered['VenueLongitude'], venues_filtered['Neighbourhood'], venues_filtered['VenueName']):
        label = folium.Popup(str(name) + ' Neighbourhood: ' + str(neigh), parse_html=True)
        folium.CircleMarker(
            [lat, lon],
            radius=5,
            popup=label,
            color='blue',
            fill=True,
            fill_color="##3186cc",
            fill_opacity=0.7).add_to(map_clusters)
        
    cluster = st.sidebar.checkbox("Cluster Neighbourhoods Based on This Venue", False)
    if not cluster:
        folium_static (map_clusters)

    if cluster:
        kclusters = st.sidebar.slider("How many Clusters would you Like?", min_value=1, max_value=5, value = 3)
        venues_new = venues_onehot.groupby(["Neighbourhood", venue]).size().reset_index(name = "Count")
        venues_merged = venues_new[venues_new[venue]!=0]
        venues_merged = venues_merged.drop(venues_merged.columns[1], axis = 1)
        venues_grouped_clustering = venues_merged.drop(["Neighbourhood"], axis=1)
        kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(venues_grouped_clustering)
        venues_merged["Cluster Labels"] = kmeans.labels_
        df=df.dropna(axis=0)
        venues_merged = venues_merged.join(df.set_index("Neighbourhood"), on="Neighbourhood")

        map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)
        rainbow = ["#8000ff", "#00b5eb", "#097636", "#ED8C20", "#df6519"]
        markers_colors = []
        for lat, lon, poi, num, cluster in zip(venues_merged['Latitude'], venues_merged['Longitude'], venues_merged['Neighbourhood'], venues_merged['Count'], venues_merged['Cluster Labels']):
            label = folium.Popup(str(poi) + ' Cluster: ' + str(cluster) + ' Count: ' + str(num), parse_html=True)
            folium.CircleMarker(
                [lat, lon],
                radius=5,
                popup=label,
                color=rainbow[cluster-1],
                fill=True,
                fill_color=rainbow[cluster-1],
                fill_opacity=0.7).add_to(map_clusters)

        folium_static(map_clusters)




        


