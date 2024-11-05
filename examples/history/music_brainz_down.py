import datetime as dt
import json
import logging as lg
import os.path
import time

import pandas as pd
import requests

pause_standard = 1.1
pause_exceeded_rate = 2

# where to save the csv output
csv_filename = "data/mb.csv"

# configure URLs and user-agent header
artist_name_url = "https://musicbrainz.org/ws/2/artist/?query=artist:{}&fmt=json"
artist_id_url = "https://musicbrainz.org/ws/2/artist/{}?fmt=json"
area_id_url = "https://musicbrainz.org/ws/2/area/{}?inc=area-rels&fmt=json"
mb_user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
headers = {"User-Agent": mb_user_agent}

# configure local caching
area_cache_filename = "data/area_cache.js"
artist_cache_filename = "data/artist_cache.js"
cache_save_frequency = 10
area_requests_count = 0
artist_requests_count = 0
area_cache = (
    json.load(open(area_cache_filename)) if os.path.isfile(area_cache_filename) else {}
)
artist_cache = (
    json.load(open(artist_cache_filename))
    if os.path.isfile(artist_cache_filename)
    else {}
)

# create a logger to capture progress
log = lg.getLogger("mb")
if not getattr(log, "handler_set", None):
    todays_date = dt.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
    log_filename = f"logs/mb_{todays_date}.log"
    handler = lg.FileHandler(log_filename, encoding="utf-8")
    formatter = lg.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(lg.INFO)
    log.handler_set = True


# make a http request to musicbrainz api and return the result
def make_request(url, headers=headers, attempt_count=1):
    global pause_standard

    time.sleep(pause_standard)
    log.info(f"request: {url}")
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        log.error(f"requests.get failed: {type(e)} {e} {response.json()}")

    if response.status_code == 200:  # if status OK
        return {"status_code": response.status_code, "json": response.json()}

    elif (
        response.status_code == 503
    ):  # if status error (server busy or rate limit exceeded)
        try:
            if "exceeding the allowable rate limit" in response.json()["error"]:
                # pause_standard = pause_standard + 0.1
                log.warning(
                    f"exceeded allowable rate limit, pause_standard is now {pause_standard} seconds"
                )
                log.warning(f"details: {response.json()}")
                time.sleep(pause_exceeded_rate)
        except:
            pass

        next_attempt_count = attempt_count + 1
        log.warning(
            f"request failed with status_code 503, so we will try it again with attempt #{next_attempt_count}"
        )
        return make_request(url, attempt_count=next_attempt_count)

    else:  # if other status code, display info and return None for caller to handle
        log.error(
            f"make_request failed: status_code {response.status_code} {response.json()}"
        )
        return None


# query the musicbrainz api for an artist's name and return the resulting id
def get_artist_id_by_name(name):
    response = make_request(artist_name_url.format(name))
    try:
        if response is not None:
            result = response["json"]
            artist_id = result["artists"][0]["id"]
            return artist_id
    except:
        log.error(f"get_artist_id_by_name error: {response}")


# parse the details of an artist from the API response
def extract_artist_details_from_response(response):
    try:
        if response is not None:
            result = response["json"]
            artist_details = {
                "id": result["id"],
                "name": result["name"],
                "type": result["type"],
                "gender": result["gender"],
                "country": result["country"],
                "begin_date": None,
                "end_date": None,
                "area_id": None,
                "area_name": None,
                "begin_area_id": None,
                "begin_area_name": None,
                "place_id": None,
                "place": None,
            }

            if (
                result["life-span"] is not None
                and "begin" in result["life-span"]
                and "end" in result["life-span"]
            ):
                artist_details["begin_date"] = result["life-span"]["begin"]
                artist_details["end_date"] = result["life-span"]["end"]
            if (
                result["area"] is not None
                and "id" in result["area"]
                and "name" in result["area"]
            ):
                artist_details["area_id"] = result["area"]["id"]
                artist_details["area_name"] = result["area"]["name"]
            if (
                result["begin_area"] is not None
                and "id" in result["begin_area"]
                and "name" in result["begin_area"]
            ):
                artist_details["begin_area_id"] = result["begin_area"]["id"]
                artist_details["begin_area_name"] = result["begin_area"]["name"]

            # populate place with begin_area_name if it's not null, else area_name if it's not null, else None
            if artist_details["begin_area_name"] is not None:
                artist_details["place"] = artist_details["begin_area_name"]
                artist_details["place_id"] = artist_details["begin_area_id"]
            elif artist_details["area_name"] is not None:
                artist_details["place"] = artist_details["area_name"]
                artist_details["place_id"] = artist_details["area_id"]

            return artist_details

    except:
        log.error(f"get_artist_by_id error: {response}")


# get an artist object from the musicbrainz api by the musicbrainz artist id
def get_artist_by_id(artist_id):
    global artist_cache, artist_requests_count

    # first, get the artist details either from the cache or from the API
    if artist_id in artist_cache:
        # if we've looked up this ID before, get it from the cache
        log.info(f"retrieving artist details from cache for ID {artist_id}")
        artist_details = artist_cache[artist_id]
    else:
        # if we haven't looked up this ID before, look it up from API now
        response = make_request(artist_id_url.format(artist_id))
        artist_details = extract_artist_details_from_response(response)

        # add this artist to the cache so we don't have to ask the API for it again
        artist_cache[artist_id] = artist_details
        log.info(f"adding artist details to cache for ID {artist_id}")

        # save the artist cache to disk once per every cache_save_frequency API requests
        artist_requests_count += 1
        if artist_requests_count % cache_save_frequency == 0:
            save_cache_to_disk(artist_cache, artist_cache_filename)

    # now that we have the artist details...
    return artist_details


# create a dataframe of artist details and place info from a list of artist IDs
def make_artists_df(artist_ids, row_labels=None, df=None, csv_save_frequency=100):
    # create a list of row labels if caller didn't pass one in
    if row_labels is None:
        row_labels = range(len(artist_ids))

    # create a new dataframe if caller didn't pass an existing one in
    cols = [
        "id",
        "name",
        "type",
        "gender",
        "country",
        "begin_date",
        "end_date",
        "begin_area_id",
        "begin_area_name",
        "area_id",
        "area_name",
        "place_id",
        "place",
    ]
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(columns=cols)

    start_time = time.time()
    for artist_id, n in zip(artist_ids, row_labels, strict=False):
        try:
            # get the artist info object
            artist = get_artist_by_id(artist_id)

            # create (or update) a df row containing the data from this artist object
            df.loc[n] = [artist[col] for col in cols]
            log.info(f"successfully got artist details #{n:,}: artist_id={artist_id}")

            # save csv dataset to disk once per every csv_save_frequency rows
            if n % csv_save_frequency == 0:
                df.to_csv(csv_filename, index=False, encoding="utf-8")

        except Exception as e:
            log.error(f"row #{n} failed: {e}")
            pass

    df.to_csv(csv_filename, index=False, encoding="utf-8")
    finish_time = time.time()
    message = f"processed {len(artist_ids):,} artists in {round(finish_time - start_time, 2):,} seconds and saved csv"
    log.info(message)
    print(message)

    return df


# parse the details of an area object from the API response
def extract_area_details_from_response(response):
    area_details = {}
    try:
        area_details["name"] = response["json"]["name"]
        if "relations" in response["json"]:
            for relation in response["json"]["relations"]:
                if (
                    relation["direction"] == "backward"
                    and relation["type"] == "part of"
                ):
                    area_details["parent_id"] = relation["area"]["id"]
                    area_details["parent_name"] = relation["area"]["name"]
        else:
            log.warning(f"area returned no relations: {result}")
        return area_details
    except Exception:
        log.error(f"extract_area_details_from_response failed: {response}")
        return None


# get details of an 'area' from the musicbrainz api by area id
def get_area(area_id, full_area_str=""):
    global area_cache, area_requests_count

    # first, get the area details either from the cache or from the API
    if area_id in area_cache:
        # if we've looked up this ID before, get it from the cache
        log.info(f"retrieving area details from cache for ID {area_id}")
        area_details = area_cache[area_id]
    else:
        # if we haven't looked up this ID before, look it up from API now
        response = make_request(area_id_url.format(area_id))
        area_details = extract_area_details_from_response(response)

        # add this area to the cache so we don't have to ask the API for it again
        area_cache[area_id] = area_details
        log.info(f"adding area details to cache for ID {area_id}")

        # save the area cache to disk once per every cache_save_frequency API requests
        area_requests_count += 1
        if area_requests_count % cache_save_frequency == 0:
            save_cache_to_disk(area_cache, area_cache_filename)

    # now that we have the area details...
    try:
        if full_area_str == "":
            full_area_str = area_details["name"]
        if "parent_name" in area_details and "parent_id" in area_details:
            full_area_str = "{}, {}".format(full_area_str, area_details["parent_name"])
            return (
                area_details["parent_id"],
                full_area_str,
            )  # recursively get parent's details
        else:
            # if no parents exist, we're done
            return None, full_area_str
    except Exception as e:
        log.error(f"get_area error: {e}")
        return None, full_area_str


# construct a full name from an area ID
# recursively traverse the API, getting coarser-grained place details each time until top-level country
def get_place_full_name_by_area_id(area_id):
    area_name = ""
    while area_id is not None:
        area_id, area_name = get_area(area_id, area_name)
    return area_name


# take a list of place IDs and return a dict linking each to its constructed full name
def get_place_full(unique_place_ids):
    start_time = time.time()
    message = f"we will attempt to get place full names for {len(unique_place_ids):,} place IDs"
    log.info(message)
    print(message)

    place_ids_names = {}
    for place_id, n in zip(
        unique_place_ids, range(len(unique_place_ids)), strict=False
    ):
        try:
            place_name = get_place_full_name_by_area_id(place_id)
        except:
            place_name = None
        place_ids_names[place_id] = place_name
        log.info(
            f'successfully created place #{n + 1:,}: "{place_name}" from place ID "{place_id}"'
        )

    message = f"finished getting place full names from place IDs in {time.time() - start_time:.2f} seconds"
    log.info(message)
    print(message)
    return place_ids_names


# find place id in dict (created by get_place_full) and return its constructed full name
def get_place_full_from_dict(place_id):
    try:
        return place_ids_names[place_id]
    except:
        return None


# save local cache object in memory to disk as JSON
def save_cache_to_disk(cache, filename):
    with open(filename, "w", encoding="utf-8") as cache_file:
        cache_file.write(json.dumps(cache))
    log.info(f"saved {len(cache.keys()):,} cached items to {filename}")


log.info("musicbrainz downloader script started")

# load the artist IDs from the lastfm scrobble history data set
scrobbles = pd.read_csv("data/lastfm_scrobbles.csv", encoding="utf-8")
artist_ids = scrobbles["artist_mbid"].dropna().unique()  # [1000:1005]
message = f"there are {len(artist_ids):,} unique artists to get details for"
log.info(message)
print(message)

# get details for each unique artist and turn results into dataframe
df = make_artists_df(artist_ids)

# get all the row labels missing in the df (due to errors that prevented row creation)
missing_row_labels = [
    label for label in range(len(artist_ids)) if label not in df.index
]

# get the artist mbid for each
row_labels_to_retry = sorted(missing_row_labels)
artist_ids_to_retry = [artist_ids[label] for label in row_labels_to_retry]

message = f"{len(artist_ids_to_retry)} artists to retry"
log.info(message)
print(message)

# get details for each artist to re-try, and turn results into dataframe
df = make_artists_df(artist_ids_to_retry, row_labels_to_retry, df)

# save to csv and show the head
df.to_csv(csv_filename, index=False, encoding="utf-8")
df[["name", "place_id", "place"]].head()

# create a dict where keys are area IDs and values are full place names from MB API
unique_place_ids = df["place_id"].dropna().unique()
place_ids_names = get_place_full(unique_place_ids)

# for each row in dataframe, pull place_full from the place_ids_names dict by place_id
df["place_full"] = df["place_id"].map(get_place_full_from_dict)
df[["name", "place_id", "place", "place_full"]].head()

# for some reason MB constructs Irish places' country as "Ireland, Ireland" - so clean up the duplicate
df["place_full"] = df["place_full"].str.replace("Ireland, Ireland", "Ireland")

# OK, one final check - see how many artist ids did not make it into the final dataframe
# first get all the rows missing place_full that have place_id
mask = (pd.isnull(df["place_full"])) & (pd.notnull(df["place_id"]))
rows_missing_place_full = list(df[mask].index)

# then get all the row labels missing in the df (due to errors that prevented row creation)
missing_row_labels = [
    label for label in range(len(artist_ids)) if label not in df.index
]

message = f"{len(missing_row_labels)} row labels are missing in the df"
log.info(message)
print(message)
message = (
    f"{len(rows_missing_place_full)} rows are missing place_full but have place_id"
)
log.info(message)
print(message)

# finish by saving the csv and cache files to disk
df.to_csv(csv_filename, index=False, encoding="utf-8")
save_cache_to_disk(area_cache, area_cache_filename)
save_cache_to_disk(artist_cache, artist_cache_filename)
