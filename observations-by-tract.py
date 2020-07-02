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


def style_function_all(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


def style_function_maj_non_white(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if x['properties']['B02001001'] == 0 or x['properties']['B02001002'] > x['properties']['B02001001'] * 0.5 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


def style_function_maj_white(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if x['properties']['B02001001'] == 0 or x['properties']['B02001002'] < x['properties']['B02001001'] * 0.5 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


def style_function_maj_black(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if x['properties']['B02001001'] == 0 or x['properties']['B02001003'] < x['properties']['B02001001'] * 0.5 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


m = folium.Map(location=[40, -75.1], zoom_start=11)

colormap = folium.LinearColormap(
    colors=["darkred", "red", "orange","yellow","lightgreen", "green", "darkgreen"],
    index=[0, 10, 50, 100, 500, 1000, 5000],
    vmin=merged_areas.loc[merged_areas['count']>0, 'count'].min(),
    vmax=merged_areas.loc[merged_areas['count']>0, 'count'].max())

tooltip_all = folium.GeoJsonTooltip(
    fields=['name',"count", 'B02001001', 'B02001002', 'B02001003'],
    aliases=['Tract Name','Observations Count', 'Total Population', 'White Only', 'Black Only'],
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_non_white = folium.GeoJsonTooltip(
    fields=['name',"count", 'B02001001', 'B02001002', 'B02001003'],
    aliases=['Tract Name','Observations Count', 'Total Population', 'White Only', 'Black Only'],
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_white = folium.GeoJsonTooltip(
    fields=['name',"count", 'B02001001', 'B02001002', 'B02001003'],
    aliases=['Tract Name','Observations Count', 'Total Population', 'White Only', 'Black Only'],
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_black = folium.GeoJsonTooltip(
    fields=['name',"count", 'B02001001', 'B02001002', 'B02001003'],
    aliases=['Tract Name','Observations Count', 'Total Population', 'White Only', 'Black Only'],
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

feature_group_all = folium.FeatureGroup(name='All')
feature_group_maj_non_white = folium.FeatureGroup(name='Majority Non-white', show=False)
feature_group_maj_white = folium.FeatureGroup(name='Majority White', show=False)
feature_group_maj_black = folium.FeatureGroup(name='Majority Black', show=False)

folium.GeoJson(merged_areas.to_json(),
               name="All",
               style_function=style_function_all,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_all,
               ).add_to(feature_group_all)

folium.GeoJson(merged_areas.to_json(),
               name="Majority Non-white",
               style_function=style_function_maj_non_white,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_maj_non_white,
               ).add_to(feature_group_maj_non_white)

folium.GeoJson(merged_areas.to_json(),
               name="Majority White",
               style_function=style_function_maj_white,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_maj_white,
               ).add_to(feature_group_maj_white)

folium.GeoJson(merged_areas.to_json(),
               name="Majority Black",
               style_function=style_function_maj_black,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_maj_black,
               ).add_to(feature_group_maj_black)

feature_group_all.add_to(m)
feature_group_maj_non_white.add_to(m)
feature_group_maj_white.add_to(m)
feature_group_maj_black.add_to(m)

folium.LayerControl().add_to(m)

m.save('maps/census_observations.html')
