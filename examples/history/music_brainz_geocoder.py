import datetime as dt
import json
import logging as lg
import os.path
import re
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from geopy.distance import great_circle
from mpl_toolkits.basemap import Basemap

# if True, discard places that are just countries if that country exists with city or state elsewhere in list
ignore_country_if_more_detail = False

# define pause durations
pause_nominatim = 0.95
pause_google = 0.15

# define input/output csv filenames
input_filename = "data/mb.csv"
output_filename = "data/mb_geocoded.csv"

# configure local caching
geocode_cache_filename = "data/geocode_cache.js"
cache_save_frequency = 10
requests_count = 0
geocode_cache = (
    json.load(open(geocode_cache_filename))
    if os.path.isfile(geocode_cache_filename)
    else {}
)

# create a logger to capture progress
log = lg.getLogger("mb_geocoder")
if not getattr(log, "handler_set", None):
    todays_date = dt.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
    log_filename = f"logs/mb_geocoder_{todays_date}.log"
    handler = lg.FileHandler(log_filename, encoding="utf-8")
    formatter = lg.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(lg.INFO)
    log.handler_set = True


# make a http request to api and return the result
def make_request(url):
    log.info(f"requesting {url}")
    return requests.get(url).json()


# use nominatim api to geocode an address and return latlng string
def geocode_nominatim(address):
    time.sleep(pause_nominatim)
    url = "https://nominatim.openstreetmap.org/search?format=json&q={}"
    data = make_request(url.format(address))
    if len(data) > 0:
        return "{},{}".format(data[0]["lat"], data[0]["lon"])


# use google maps api to geocode an address and return latlng string
def geocode_google(address):
    time.sleep(pause_google)
    url = "http://maps.googleapis.com/maps/api/geocode/json?sensor=false&address={}"
    data = make_request(url.format(address))
    if len(data["results"]) > 0:
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        return f"{lat},{lng}"


# handle geocoding, either from local cache or from one of defined geocoding functions that call APIs
def geocode(address, geocode_function=geocode_nominatim, use_cache=True):
    global geocode_cache, requests_count

    if use_cache and address in geocode_cache and pd.notnull(geocode_cache[address]):
        log.info(f'retrieving lat-long from cache for place "{address}"')
        return geocode_cache[address]
    else:
        requests_count += 1
        latlng = geocode_function(address)
        geocode_cache[address] = latlng
        log.info(f'stored lat-long in cache for place "{address}"')

        if requests_count % cache_save_frequency == 0:
            save_cache_to_disk(geocode_cache, geocode_cache_filename)

        return latlng


# to improve geocoding accuracy, remove anything in parentheses or square brackets
# example: turn 'Tarlac, Luzon (Region III), Philippines' into 'Tarlac, Luzon, Philippines'
regex = re.compile("\\(.*\\)|\\[.*\\]")


def clean_place_full(place_full):
    if isinstance(place_full, str):
        return regex.sub("", place_full).replace(" ,", ",").replace("  ", " ")


# parse out the country name in strings with greater geographic detail
def get_country_if_more_detail(address):
    tokens = address.split(",")
    if len(tokens) > 1:
        return tokens[-1].strip()


# save local cache object in memory to disk as JSON
def save_cache_to_disk(cache, filename):
    with open(filename, "w", encoding="utf-8") as cache_file:
        cache_file.write(json.dumps(cache))
    log.info(f"saved {len(cache.keys()):,} cached items to {filename}")


# how far apart are the lat-longs returned from Google and Nominatim for Brixton?
address = "Brixton, London, England, United Kingdom"
latlng_google = geocode(address, geocode_google, use_cache=False)
latlng_nominatim = geocode(address, geocode_nominatim, use_cache=False)

print(f"{latlng_google} google")
print(f"{latlng_nominatim} nominatim")
print(f"{great_circle(latlng_google, latlng_nominatim).m:.1f} meters apart")

# load the dataset
artists = pd.read_csv(input_filename, encoding="utf-8")
print(f"{len(artists):,} total artists")

# clean place_full to remove anything in parentheses or brackets and change empty strings to nulls
artists["place_full"] = artists["place_full"].map(clean_place_full)
artists.loc[artists["place_full"] == "", "place_full"] = None

# drop nulls and get the unique set of places
addresses = pd.Series(artists["place_full"].dropna().sort_values().unique())
print(f"{len(addresses):,} unique places")

# only keep places that are just countries if that country does not exist with city or state elsewhere in list
if ignore_country_if_more_detail:
    countries_with_more_detail = pd.Series(
        addresses.map(get_country_if_more_detail).dropna().sort_values().unique()
    )
    print(f"{len(countries_with_more_detail):,} countries with more detail")
    addresses_to_geocode = addresses[~addresses.isin(countries_with_more_detail)]
    print(f"{len(addresses_to_geocode):,} unique addresses to geocode")
else:
    addresses_to_geocode = addresses

# geocode (with nominatim) each retained address (ie, full place name string)
start_time = time.time()
latlng_dict = {}
for address in addresses_to_geocode:
    latlng_dict[address] = geocode(address, geocode_function=geocode_nominatim)

print(
    f"geocoded {len(addresses_to_geocode):,} addresses in {int(time.time() - start_time):,.2f} seconds"
)
print(
    f"received {len([key for key in latlng_dict if latlng_dict[key] is not None]):,} non-null lat-longs"
)

# which addresses failed to geocode successfully?
addresses_to_geocode = [key for key in latlng_dict if latlng_dict[key] is None]
print(f"{len(addresses_to_geocode)} addresses still lack lat-long")

# now geocode (with google) each address that failed
start_time = time.time()
for address in addresses_to_geocode:
    latlng_dict[address] = geocode(address, geocode_function=geocode_google)

print(
    f"geocoded {len(addresses_to_geocode):,} addresses in {int(time.time() - start_time):,.2f} seconds"
)
print(
    f"received {len([key for key in latlng_dict if latlng_dict[key] is not None]):,} non-null lat-longs"
)


# for each artist, if their place appears in the geocoded dict, pull the latlng value from dict into new df column
def get_latlng_by_address(address):
    try:
        return latlng_dict[address]
    except:
        return None


artists["place_latlng"] = artists["place_full"].map(get_latlng_by_address)
artists[["name", "place_full", "place_latlng"]].sort_values(by="place_full").head()

# all done, save everything
save_cache_to_disk(geocode_cache, geocode_cache_filename)
artists.to_csv(output_filename, index=False, encoding="utf-8")

# get discrete vectors of lats and lons, for easy x-y scatter-plotting
unique_latlngs = artists["place_latlng"].dropna().drop_duplicates()
lats = unique_latlngs.map(lambda x: float(x.split(",")[0]))
lons = unique_latlngs.map(lambda x: float(x.split(",")[1]))

# define map colors
land_color = "#f5f5f3"
water_color = "#cdd2d4"
coastline_color = "#f5f5f3"
border_color = "#bbbbbb"
meridian_color = "#f5f5f3"
marker_fill_color = "#cc3300"
marker_edge_color = "None"

# create the plot
fig = plt.figure(figsize=(20, 10))
ax = fig.add_subplot(111, facecolor="#ffffff", frame_on=False)
ax.set_title("Last.fm Artist Origins", fontsize=24, color="#333333")

# draw the basemap and its features
m = Basemap(projection="kav7", lon_0=0, resolution="l", area_thresh=10000)
m.drawmapboundary(color=border_color, fill_color=water_color)
m.drawcoastlines(color=coastline_color)
m.drawcountries(color=border_color)
m.fillcontinents(color=land_color, lake_color=water_color)
m.drawparallels(np.arange(-90.0, 120.0, 30.0), color=meridian_color)
m.drawmeridians(np.arange(0.0, 420.0, 60.0), color=meridian_color)

# project our points from each dataset then concatenate and scatter plot them
x, y = m(lons.values, lats.values)
m.scatter(
    x, y, s=8, color=marker_fill_color, edgecolor=marker_edge_color, alpha=0.9, zorder=3
)

# show the map
plt.savefig(
    "images/lastfm_artists_origins_map.png", dpi=96, bbox_inches="tight", pad_inches=0.2
)
plt.show()
