import json
import math
import random

import pandas as pd
from IPython.display import IFrame

# load the geocoded data set of artists
df = pd.read_csv("data/mb_geocoded.csv", encoding="utf-8")
print(f"{len(df):,} total rows")
df = df[pd.notnull(df["place_latlng"])]
print(f"{len(df):,} rows with lat-long")
print("{:,} unique lat-longs".format(len(df["place_latlng"].unique())))

# determine how many times each place appears in dataset, and break latlng into discrete lat and long
place_counts = df["place_full"].value_counts()
df["place_count"] = df["place_full"].map(lambda x: place_counts[x])
df["lat"] = df["place_latlng"].map(lambda x: x.split(",")[0])
df["lng"] = df["place_latlng"].map(lambda x: x.split(",")[1])
df = df[["name", "place_full", "place_count", "lat", "lng"]]
df.head()

# create html list of artists from each place
features = []
for place_full in df["place_full"].unique():
    # how many artists to show before saying "...and n more"
    num_to_show = 3
    line_break = "<br />"
    artists = ""

    place_count = place_counts[place_full]
    names = df[df["place_full"] == place_full]["name"]

    if place_count <= num_to_show:
        for name in names:
            artists = f"{artists}{name}{line_break}"

    else:
        for name in names[0:num_to_show]:
            artists = f"{artists}{name}{line_break}"
        artists = f"{artists}...and {place_count - num_to_show:,} more"

    features.append([place_full, artists])

df_leaflet = pd.DataFrame(features, columns=["place_full", "artists"])

# strip off any tailing (and hence unnecessary) line breaks at the end of the artists list
# can't use str.strip for this because it strips characters: artist names would lose trailing b's and r's
df_leaflet["artists"] = df_leaflet["artists"].map(
    lambda x: x[: -len(line_break)] if x.endswith(line_break) else x
)


# jitter either a lat or a lng within KMs of original
def jitter(val, kms=0.5):
    earth_radius = 6378.16
    one_degree = (2 * math.pi * earth_radius) / 360
    one_km = 1 / one_degree
    lower_range = val - (kms * one_km)
    upper_range = val + (kms * one_km)
    return random.random() * (upper_range - lower_range) + lower_range


# add lat and long back to the dataframe
place_lat_lng = {}
df_unique = df[["place_full", "lat", "lng"]].drop_duplicates(subset="place_full")
for label in df_unique.index:
    place_lat_lng[df_unique.loc[label, "place_full"]] = (
        df_unique.loc[label, "lat"],
        df_unique.loc[label, "lng"],
    )

# extract lat & lng, convert to float, jitter, and round to 7 decimal places
df_leaflet["lat"] = df_leaflet["place_full"].map(
    lambda x: f"{jitter(float(place_lat_lng[x][0])):.7f}"
)
df_leaflet["lng"] = df_leaflet["place_full"].map(
    lambda x: f"{jitter(float(place_lat_lng[x][1])):.7f}"
)
df_leaflet.head()


# function to write the dataframe out to geojson
def df_to_geojson(df, properties, lat="latitude", lon="longitude"):
    # create a new python dict to contain our geojson data, using geojson format
    geojson = {"type": "FeatureCollection", "features": []}

    # loop through each row in the dataframe and convert each row to geojson format
    for _, row in df.iterrows():
        # create a feature template to fill in
        feature = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": []},
        }

        # fill in the coordinates
        feature["geometry"]["coordinates"] = [row[lon], row[lat]]

        # for each column, get the value and add it as a new feature property
        for prop in properties:
            feature["properties"][prop] = row[prop]

        # add this feature (aka, converted dataframe row) to the list of features inside our dict
        geojson["features"].append(feature)

    return geojson


geojson = df_to_geojson(df_leaflet, df_leaflet.columns, lat="lat", lon="lng")

# save the geojson result to a file
output_filename = "leaflet/lastfm-dataset.js"
with open(output_filename, "w") as output_file:
    output_file.write(
        "var dataset={};".format(json.dumps(geojson, separators=(",", ":")))
    )

# how many features did we save to the geojson file?
print("{:,} geotagged features saved to file".format(len(geojson["features"])))

# show the iframe of the leaflet web map here
IFrame("leaflet/lastfm-artists-map.html", width=600, height=400)
