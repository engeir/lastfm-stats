"""Download and update Lastfm scrobbles."""

import time

import pandas as pd
import requests

from lastfm.config import API_KEY, USER_NAME


class GetScrobbles:
    """Download and update your scrobbles CSV."""

    def __init__(self):
        self.pause_duration = 0.2
        self.ds = self._load_csv()
        self.existing_items = set(self.ds["timestamp"].tolist())
        self.method = "recenttracks"

    def _load_csv(self) -> pd.DataFrame:
        """Read the existing CSV file into a pandas DataFrame or create a new."""
        try:
            existing_df = pd.read_csv("data/lastfm_scrobbles.csv")
        except FileNotFoundError:
            existing_df = pd.DataFrame()
        return existing_df

    def get_scrobbles(self, limit=200, extended=0, page=1, pages=0):
        """Get scrobbles via the lastfm API.

        Parameters
        ----------
        limit: api lets you retrieve up to 200 records per call
        extended: api lets you retrieve extended data for each track, 0=no, 1=yes
        page: page of results to start retrieving at
        pages: how many pages of results to retrieve. if 0, get as many as api can return.
        """
        # initialize url and lists to contain response fields
        url = "https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&page={}&format=json"
        artist_names = []
        artist_mbids = []
        album_names = []
        album_mbids = []
        track_names = []
        track_mbids = []
        timestamps = []

        # make first request, just to get the total number of pages
        request_url = url.format(self.method, USER_NAME, API_KEY, limit, extended, page)
        response = requests.get(request_url).json()
        total_pages = int(response[self.method]["@attr"]["totalPages"])
        if pages > 0:
            total_pages = min([total_pages, pages])

        print(f"{total_pages} total pages to retrieve")

        # request each page of data one at a time
        found_existing = False
        for page in range(1, int(total_pages) + 1, 1):
            # if not page % 22:
            #     break
            print(f"Page {page}/{total_pages}", end="\r")
            # time.sleep(self.pause_duration)
            request_url = url.format(
                self.method, USER_NAME, API_KEY, limit, extended, page
            )
            response = requests.get(request_url)
            scrobbles = response.json()
            for scrobble in scrobbles[self.method]["track"]:
                # Only retain completed scrobbles (aka, with timestamp and not 'now
                # playing'). Also check if it has been downloaded already.
                if (
                    "date" in scrobble.keys()
                    and int(scrobble["date"]["uts"]) not in self.existing_items
                ):
                    artist_names.append(scrobble["artist"]["#text"])
                    artist_mbids.append(scrobble["artist"]["mbid"])
                    album_names.append(scrobble["album"]["#text"])
                    album_mbids.append(scrobble["album"]["mbid"])
                    track_names.append(scrobble["name"])
                    track_mbids.append(scrobble["mbid"])
                    timestamps.append(int(scrobble["date"]["uts"]))
                elif int(scrobble["date"]["uts"]) in self.existing_items:
                    found_existing = True
            if found_existing:
                break

        if not artist_names:
            print("Scrobbles are up to date!")
            return
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

        updated_df = pd.concat([self.ds, df], ignore_index=True)
        self.ds = updated_df.sort_values(by="timestamp", ascending=False).reset_index(
            drop=True
        )

    def save(self):
        """Save the new daataset."""
        self.get_scrobbles()
        self.ds.to_csv("data/lastfm_scrobbles.csv", index=None, encoding="utf-8")


if __name__ == "__main__":
    down = GetScrobbles()
    # print(down.existing_items)
    down.save()
