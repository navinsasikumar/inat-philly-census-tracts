import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from fiona.crs import from_epsg
import pysal
import folium

# 1 - Census Tracts
geojson_file_race = "data/acs2018_5yr_B02001_14000US42101038300.geojson"
tracts_race = gpd.read_file(geojson_file_race)
tracts_race = tracts_race[tracts_race.name != 'Philadelphia County, PA']

# 2 - iNat data
observations = pd.read_csv("data/observations-96672.csv")

# 3 - convert to Geopandas Geodataframe
gdf_observations = gpd.GeoDataFrame(observations, geometry=gpd.points_from_xy(observations.longitude, observations.latitude))
gdf_observations.crs = from_epsg(4326)
gdf_observations.crs = {'init': 'epsg:4326'}

# 4 - Join data
sjoined_observations = gpd.sjoin(gdf_observations, tracts_race, op="within", how="right")

grouped = sjoined_observations.groupby("name").size()
df = grouped.to_frame().reset_index()
df.columns = ['name', 'observations_count']

print (df.sort_values('observations_count'))

grouped = sjoined_observations.groupby("name")["id"].agg(['count'])
print (grouped.sort_values('count'))

merged_areas = tracts_race.merge(grouped, on='name', how='outer')

vmin, vmax = 100, 1000
fig, ax = plt.subplots(1, figsize=(10, 12))
ax.axis('off')
ax.set_title('iNat Observations by Census Tract', fontdict={'fontsize': '25', 'fontweight' : '3'})

# sm = plt.cm.ScalarMappable(cmap='Greens', norm=plt.Normalize(vmin=vmin, vmax=vmax))
# sm._A = []
# cbar = fig.colorbar(sm)

# merged_areas.plot(column='count', cmap = 'Greens', legend =  True, linewidth=0.8, edgecolor='0.8', ax=ax, scheme="quantiles", k=30)
# merged_areas.plot(column='count', cmap = 'Greens', legend =  True, linewidth=0.8, edgecolor='0.8', ax=ax, scheme="User_Defined", classification_kwds=dict(bins=[0,10,50,100,200,300,400,500,750,1000,1500,2000,3000,5000]))

m = folium.Map(location=[40, -75.1], zoom_start=11)
# bins = list(merged_areas['count'].quantile([0,0.05,0.1,0.2,0.5,0.75,0.9,0.95,0.98,1]))
# choropleth = folium.Choropleth(geo_data=merged_areas.to_json(),
                  # data=merged_areas,
                  # key_on='feature.properties.name',
                  # columns=['name', 'count'],
                  # fill_color='Greens',
                  # bins=bins,
                  # reset=True
                 # ).add_to(m)

# folium.GeoJsonPopup(fields=['name', 'count', 'B02001001']).add_to(choropleth.geojson)

colormap = folium.LinearColormap(
    colors=["darkred", "red", "orange","yellow","lightgreen", "green", "darkgreen"],
    index=[0, 10, 50, 100, 500, 1000, 5000],
    vmin=merged_areas.loc[merged_areas['count']>0, 'count'].min(),
    vmax=merged_areas.loc[merged_areas['count']>0, 'count'].max())

folium.GeoJson(merged_areas.to_json(),
               name="Philadelphia",
               style_function=lambda x: {"weight":1, 'color':'black','fillColor':colormap(x['properties']['count']), 'fillOpacity':0.7},
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=folium.GeoJsonTooltip(
        fields=['name',"count", 'B02001001', 'B02001002', 'B02001003'],
        aliases=['Tract Name','Observations Count', 'Total Population', 'White Only', 'Black Only'],
        sticky=True,
        style="font-family: courier new; color: steelblue;",
        opacity=0.8,
        direction='top'),
              ).add_to(m)

m.save('census_observations.html')
