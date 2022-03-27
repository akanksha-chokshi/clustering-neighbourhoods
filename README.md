# clustering-neighbourhoods
**How is the data obtained?**

1. I scrape the Wikipedia page of neighbourhoods in London to get all the neighbourhoods in London using BeautifulSoup. 
2. I then use Geocoder from ArcGIS to obtain the latitudinal and longitudinal coordinates of each neighbourhood. 
3. Next, I use the Foursquare API to obtain details of ‘venues’ or landmarks for each neighbourhood.

Hence, the data is obtained through web scraping, a GIS package and API calls to Foursquare.

**What next?**

I process the data using pandas and numpy. Based on the user’s query (whether they want to explore a venue or neighbourhood + additional filters they wish to apply), I apply the respective queries to the dataframe. I then render and visualise the results using Folium, a geospatial data visualisation package.

I also display relevant information like most and least popular neighbourhoods for the chosen venue and vice versa so the user knows what to expect from the visualisation, i.e. not choose a neighbourhood with no occurrence of the venue they are looking for.

**What else?**

I applied K-Means Clustering from the scikit-learn library to the neighbourhoods data based on the venue the user chooses. This divides neighbourhoods into three categories: one where that venue occurs very frequently, one where it occurs with medium frequency and one with little to no frequency. Users can visualise these clusters on the map and know the actual number of venues in each neighbourhood as well.

**Why Cluster?**

Some venues like parks are more common than, say, skating rinks. Clustering neighbourhoods by venue gives users the idea of how a neighbourhood compares to others specifically given the frequency distribution of that particular venue.
