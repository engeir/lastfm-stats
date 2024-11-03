"""Download and update Lastfm scrobbles."""

import pandas as pd
import requests

from .config import API_KEY, USER_NAME
from .tools import DATA_PATH


class GetScrobbles:
    """Download and update your scrobbles CSV."""

    def __init__(self):
        self.pause_duration = 0.2
        self.ds = self._load_csv()
        self.existing_items = self._get_items()
        self.method = "recenttracks"

    def _load_csv(self) -> pd.DataFrame:
        """Read the existing CSV file into a pandas DataFrame or create a new."""
        try:
            existing_df = pd.read_csv(DATA_PATH / "lastfm_scrobbles.csv")
        except FileNotFoundError:
            existing_df = pd.DataFrame()
        return existing_df

    def _get_items(self) -> set:
        try:
            items = set(self.ds["timestamp"].tolist())
        except KeyError:
            items = set()
        return items

    def get_scrobbles(
        self, limit: int = 200, extended: int = 0, page: int = 1, pages: int = 0
    ) -> None:
        """Get scrobbles via the lastfm API.

        Parameters
        ----------
        limit : int
            The API lets you retrieve up to 200 records per call
        extended : int
            Th API lets you retrieve extended data for each track, 0=no, 1=yes
        page : int
            The page of results to start retrieving at
        pages : int
            The number of pages of results to retrieve. if 0, get as many as api can
            return.
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
        for page_ in range(1, int(total_pages) + 1):
            # if not page % 22:
            #     break
            print(f"Page {page_}/{total_pages}", end="\r")
            # time.sleep(self.pause_duration)
            request_url = url.format(
                self.method, USER_NAME, API_KEY, limit, extended, page_
            )
            response = requests.get(request_url)
            scrobbles = response.json()
            for scrobble in scrobbles[self.method]["track"]:
                # Only retain completed scrobbles (aka, with timestamp and not 'now
                # playing'). Also check if it has been downloaded already.
                if "@attr" in scrobble and scrobble["@attr"]["nowplaying"] == "true":
                    continue
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
        self._add_to_dataframe(
            (artist_names, artist_mbids),
            (album_names, album_mbids),
            (track_names, track_mbids),
            timestamps,
        )

    def _add_to_dataframe(
        self,
        artist: tuple[list, list],
        album: tuple[list, list],
        track: tuple[list, list],
        timestamps: list,
    ) -> None:
        # create and populate a dataframe to contain the data
        df = pd.DataFrame()
        df["artist"] = artist[0]
        df["artist_mbid"] = artist[1]
        df["album"] = album[0]
        df["album_mbid"] = album[1]
        df["track"] = track[0]
        df["track_mbid"] = track[1]
        df["timestamp"] = timestamps
        df["datetime"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")

        updated_df = pd.concat([self.ds, df], ignore_index=True)
        self.ds = updated_df.sort_values(by="timestamp", ascending=False).reset_index(
            drop=True
        )

    def save(self):
        """Save the new daataset."""
        self.get_scrobbles()
        self.ds.to_csv(DATA_PATH / "lastfm_scrobbles.csv", index=None, encoding="utf-8")


if __name__ == "__main__":
    down = GetScrobbles()
    # print(down.existing_items)
    down.save()
