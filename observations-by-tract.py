mport geopandas as gpd
import matplotlib.pyplot as plt
from fiona.crs import from_epsg
import pysal
import folium

# 1 - Census Tracts
geojson_file_race = "data/acs2018_5yr_B02001_14000US42101038300.geojson"
tracts_race = gpd.read_file(geojson_file_race)
tracts_race = tracts_race[tracts_race.name != 'Philadelphia County, PA']

geojson_file_ethnicity = "data/acs2018_5yr_B03003_14000US42101038300.geojson"
tracts_ethnicity = gpd.read_file(geojson_file_ethnicity)
tracts_ethnicity = tracts_ethnicity[tracts_ethnicity.name != 'Philadelphia County, PA']

geojson_file_income = "data/acs2018_5yr_B19001_14000US42101038300.geojson"
tracts_income = gpd.read_file(geojson_file_income)
tracts_income = tracts_income[tracts_income.name != 'Philadelphia County, PA']

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
merged_areas = merged_areas.merge(tracts_ethnicity[[
            'name',
            'B03003001',
            'B03003003',
        ]], on='name', how='outer')
merged_areas = merged_areas.merge(tracts_income[[
            'name',
            'B19001001',
            'B19001002',
            'B19001003',
            'B19001004',
            'B19001005',
            'B19001006',
            'B19001007',
            'B19001008',
            'B19001009',
            'B19001010',
            'B19001011',
            'B19001012',
            'B19001013',
            'B19001014',
            'B19001015',
            'B19001016',
            'B19001017',
        ]], on='name', how='outer')


def get_race_pct(col):
    return merged_areas.B02001001.where(
        merged_areas.B02001001 == 0,
        round((merged_areas[col] / merged_areas.B02001001 * 100), 2)
    )


def get_ethnicity_pct(col):
    return merged_areas.B03003001.where(
        merged_areas.B03003001 == 0,
        round((merged_areas[col] / merged_areas.B03003001 * 100), 2)
    )


def get_income_pct(cols):
    sum = 0
    for col in cols:
        sum += merged_areas[col]

    return merged_areas.B19001001.where(
        merged_areas.B19001001 == 0,
        round((sum / merged_areas.B19001001 * 100), 2)
    )


merged_areas['non_white_pct'] = merged_areas.B02001001.where(
    merged_areas.B02001001 == 0,
    round(100 - (merged_areas.B02001002 / merged_areas.B02001001 * 100), 2)
)
merged_areas['white_pct'] = get_race_pct('B02001002')
merged_areas['black_pct'] = get_race_pct('B02001003')
merged_areas['native_pct'] = get_race_pct('B02001004')
merged_areas['asian_pct'] = get_race_pct('B02001005')
merged_areas['islander_pct'] = get_race_pct('B02001006')

merged_areas['hispanic_pct'] = get_race_pct('B03003003')

merged_areas['under_50k'] = get_income_pct(['B19001002', 'B19001003', 'B19001004', 'B19001005', 'B19001006', 'B19001007', 'B19001008', 'B19001009','B19001010'])
merged_areas['50k_to_100k'] = get_income_pct(['B19001011', 'B19001012', 'B19001013'])
merged_areas['100k_to_200k'] = get_income_pct(['B19001014', 'B19001015', 'B19001016'])
merged_areas['over_200k'] = get_income_pct(['B19001017'])


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


def style_function_maj_hispanic(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if x['properties']['hispanic_pct'] < 50 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


def style_function_maj_under_50k(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if x['properties']['under_50k'] < 50 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


def style_function_maj_over_50k(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if x['properties']['under_50k'] > 50 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


def style_function_40pct_over_100k(x):
    return {
        "weight":1,
        'color':'black',
        'fillColor':'#black' if (x['properties']['100k_to_200k'] + x['properties']['over_200k']) < 40 else colormap(x['properties']['count']),
        'fillOpacity':0.7
    }


m = folium.Map(location=[40, -75.1], zoom_start=11)

colormap = folium.LinearColormap(
    colors=["darkred", "red", "orange","yellow","lightgreen", "green", "darkgreen"],
    index=[0, 10, 50, 100, 500, 1000, 5000],
    vmin=merged_areas.loc[merged_areas['count']>0, 'count'].min(),
    vmax=merged_areas.loc[merged_areas['count']>0, 'count'].max())

fields = ['name', 'count', 'B02001001', 'non_white_pct', 'white_pct', 'black_pct', 'hispanic_pct', 'native_pct', 'asian_pct', 'islander_pct', 'under_50k', '50k_to_100k', '100k_to_200k', 'over_200k']
aliases = ['Tract Name','Observations Count', 'Total Population', 'Non-White %', 'White %', 'Black or African American %', 'Hispanic or Latino %', 'American Indian and Alaska Native %', 'Asian %', 'Native Hawaiian and Other Pacific Islander %', 'Under $50k', '$50k-$100k', '$100k-$200k', 'Over $200k']

tooltip_all = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_non_white = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_white = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_black = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_hispanic = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_under_50k = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_maj_over_50k = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

tooltip_40pct_over_100k = folium.GeoJsonTooltip(
    fields=fields,
    aliases=aliases,
    sticky=True,
    style="font-family: courier new; color: steelblue;",
    opacity=0.8,
    direction='top'
)

feature_group_all = folium.FeatureGroup(name='All')
feature_group_maj_non_white = folium.FeatureGroup(name='Majority Non-white', show=False)
feature_group_maj_white = folium.FeatureGroup(name='Majority White', show=False)
feature_group_maj_black = folium.FeatureGroup(name='Majority Black', show=False)
feature_group_maj_hispanic = folium.FeatureGroup(name='Majority Hispanic or Latino', show=False)
feature_group_maj_under_50k = folium.FeatureGroup(name='Household Income: Majority Under 50k', show=False)
feature_group_maj_over_50k = folium.FeatureGroup(name='Household Income: Majority Over 50k', show=False)
feature_group_40pct_over_100k = folium.FeatureGroup(name='Household Income: 40% Over 100k', show=False)

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

folium.GeoJson(merged_areas.to_json(),
               name="Majority Hispanic or Latino",
               style_function=style_function_maj_hispanic,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_maj_hispanic,
               ).add_to(feature_group_maj_hispanic)

folium.GeoJson(merged_areas.to_json(),
               name="Majority Under 50k",
               style_function=style_function_maj_under_50k,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_maj_under_50k,
               ).add_to(feature_group_maj_under_50k)

folium.GeoJson(merged_areas.to_json(),
               name="Majority Over 50k",
               style_function=style_function_maj_over_50k,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_maj_over_50k,
               ).add_to(feature_group_maj_over_50k)

folium.GeoJson(merged_areas.to_json(),
               name="40% Over 100k",
               style_function=style_function_40pct_over_100k,
               highlight_function=lambda x: {'weight':2, 'color':'black'},
               tooltip=tooltip_40pct_over_100k,
               ).add_to(feature_group_40pct_over_100k)

feature_group_all.add_to(m)
feature_group_maj_non_white.add_to(m)
feature_group_maj_white.add_to(m)
feature_group_maj_black.add_to(m)
feature_group_maj_hispanic.add_to(m)
feature_group_maj_under_50k.add_to(m)
feature_group_maj_over_50k.add_to(m)
feature_group_40pct_over_100k.add_to(m)

folium.LayerControl().add_to(m)

m.save('maps/census_observations.html')
