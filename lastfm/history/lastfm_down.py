import time

import pandas as pd
import requests

from .config import API_KEY, USER_NAME

# how long to pause between consecutive API requests
pause_duration = 0.2

url = "https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&page={}&format=json"
limit = 200  # api lets you retrieve up to 200 records per call
extended = 0  # api lets you retrieve extended data for each track, 0=no, 1=yes
page = 1  # page of results to start retrieving at

method = "toptracks"
request_url = url.format(method, USER_NAME, API_KEY, limit, extended, page)
artist_names = []
track_names = []
play_counts = []
response = requests.get(request_url).json()
for item in response[method]["track"]:
    artist_names.append(item["artist"]["name"])
    track_names.append(item["name"])
    play_counts.append(item["playcount"])

top_tracks = pd.DataFrame()
top_tracks["artist"] = artist_names
top_tracks["track"] = track_names
top_tracks["play_count"] = play_counts
top_tracks.to_csv("data/lastfm_top_tracks.csv", index=None, encoding="utf-8")
top_tracks.head()

method = "topartists"
request_url = url.format(method, USER_NAME, API_KEY, limit, extended, page)
artist_names = []
play_counts = []
response = requests.get(request_url).json()
for item in response[method]["artist"]:
    artist_names.append(item["name"])
    play_counts.append(item["playcount"])

top_artists = pd.DataFrame()
top_artists["artist"] = artist_names
top_artists["play_count"] = play_counts
top_artists.to_csv("data/lastfm_top_artists.csv", index=None, encoding="utf-8")
top_artists.head()

method = "topalbums"
request_url = url.format(method, USER_NAME, API_KEY, limit, extended, page)
artist_names = []
album_names = []
play_counts = []
response = requests.get(request_url).json()
for item in response[method]["album"]:
    artist_names.append(item["artist"]["name"])
    album_names.append(item["name"])
    play_counts.append(item["playcount"])

top_albums = pd.DataFrame()
top_albums["artist"] = artist_names
top_albums["album"] = album_names
top_albums["play_count"] = play_counts
top_albums.to_csv("data/lastfm_top_albums.csv", index=None, encoding="utf-8")
top_albums.head()


def get_scrobbles(
    method="recenttracks",
    username=USER_NAME,
    key=API_KEY,
    limit=200,
    extended=0,
    page=1,
    pages=0,
):
    """Download scrobbles from last.fm.

    Parameters
    ----------
    method : api method.
    username/key : api credentials
    limit : api lets you retrieve up to 200 records per call
    extended : api lets you retrieve extended data for each track, 0=no, 1=yes
    page : page of results to start retrieving at
    pages : how many pages of results to retrieve. if 0, get as many as api can return.
    """
    # initialize url and lists to contain response fields
    url = "https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&page={}&format=json"
    responses = []
    artist_names = []
    artist_mbids = []
    album_names = []
    album_mbids = []
    track_names = []
    track_mbids = []
    timestamps = []

    # make first request, just to get the total number of pages
    request_url = url.format(method, username, key, limit, extended, page)
    response = requests.get(request_url).json()
    total_pages = int(response[method]["@attr"]["totalPages"])
    if pages > 0:
        total_pages = min([total_pages, pages])

    print(f"{total_pages} total pages to retrieve")

    # request each page of data one at a time
    for page in range(1, int(total_pages) + 1, 1):
        if page % 10 == 0:
            print(page, end=" ")
        time.sleep(pause_duration)
        request_url = url.format(method, username, key, limit, extended, page)
        responses.append(requests.get(request_url))

    # parse the fields out of each scrobble in each page (aka response) of scrobbles
    for response in responses:
        scrobbles = response.json()
        for scrobble in scrobbles[method]["track"]:
            # only retain completed scrobbles (aka, with timestamp and not 'now playing')
            if "date" in scrobble.keys():
                artist_names.append(scrobble["artist"]["#text"])
                artist_mbids.append(scrobble["artist"]["mbid"])
                album_names.append(scrobble["album"]["#text"])
                album_mbids.append(scrobble["album"]["mbid"])
                track_names.append(scrobble["name"])
                track_mbids.append(scrobble["mbid"])
                timestamps.append(scrobble["date"]["uts"])

    # create and populate a dataframe to contain the data
    df = pd.DataFrame()
    df["artist"] = artist_names
    df["artist_mbid"] = artist_mbids
    df["album"] = album_names
    df["album_mbid"] = album_mbids
    df["track"] = track_names
    df["track_mbid"] = track_mbids
    df["timestamp"] = timestamps
    df["datetime"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")

    return df


# get all scrobbled tracks ever, in order of recency (pages=0 to get all)
scrobbles = get_scrobbles(pages=0)

# save the dataset
scrobbles.to_csv("data/lastfm_scrobbles.csv", index=None, encoding="utf-8")
print(f"{len(scrobbles):,} total rows")
scrobbles.head()
