"""Search CSV file for stats about an artist and a song."""

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from ..tools import DATA_PATH


class CurrentStats:
    """Download and update your scrobbles CSV."""

    def __init__(self):
        self.pause_duration = 0.2
        self.ds = self._load_csv()

    def _load_csv(self) -> pd.DataFrame:
        """Read the existing CSV file into a pandas DataFrame or create a new."""
        try:
            existing_df = pd.read_csv(DATA_PATH / "lastfm_scrobbles.csv")
        except FileNotFoundError:
            existing_df = pd.DataFrame()
        return existing_df

    def listening_history(self, artist: str) -> px.line:
        # TODO: dont show before 2010 or something
        df = self.ds[self.ds["artist"] == artist]
        df["cumulative_count"] = range(1, len(df) + 1)[::-1]
        # df["datetime"] = pd.to_datetime(df["datetime"])
        df.loc[:, ("datetime")] = pd.to_datetime(df.loc[:, ("datetime")])
        fig = px.line(df, x="datetime", y="cumulative_count", title="Listening history")
        fig.update_layout(
            title_x=0.5,
            xaxis_title="Time",
            yaxis_title="Count",
            showlegend=True,
            title_font_family="Open Sans",
            title_font_size=25,
        )
        return fig

    def top_songs(self, artist: str) -> px.line:
        df = self.ds[self.ds["artist"] == artist]
        unique_songs = set(df["track"])
        song_counts = df.loc[:, ("track")].value_counts()[::-1].reset_index()
        length = max(len(unique_songs) * 30, 100)
        fig = px.bar(
            song_counts,
            x="count",
            y="track",
            orientation="h",
            title="Top songs",
            height=length,
        )
        fig.update_layout(
            title_x=0.5,
            xaxis_title="Count",
            yaxis_title="Track",
            showlegend=True,
            title_font_family="Open Sans",
            title_font_size=25,
        )
        return fig


if __name__ == "__main__":
    s = CurrentStats()
    coil = s.ds[s.ds["artist"] == "Coil"]
    ll = len(coil)
    # coil.loc[:, ("cumulative_count")] = range(1, len(coil) + 1)[::-1]
    coil.loc.__setitem__((slice(None), ("cumulative_count")), range(1, ll + 1)[::-1])
    coil.loc[:, ("datetime")] = pd.to_datetime(coil.loc[:, ("datetime")])
    # fig = px.line(coil, x="datetime", y="track", title="Life expectancy in Canada")
    # fig.show()
    plt.plot(
        coil["datetime"], coil["cumulative_count"], marker="", linestyle="-", color="b"
    )
    plt.title("Songs listened to over time by Coil")
    plt.xlabel("Date and Time")
    plt.ylabel("Listening count")
    plt.xticks(rotation=45)  # Rotate song labels for better readability
    plt.tight_layout()  # Adjust layout to not cut off labels

    plt.figure()
    song_counts = coil.loc[:, ("track")].value_counts().head(15)[::-1]
    song_df = song_counts.to_frame(name="song_counts")
    song_counts_df = song_counts.reset_index()
    # print(type(coil))
    # print(type(song_counts))
    # print(type(song_df))
    # print(song_counts)
    # print(song_df)
    # print(song_counts_df)
    song_counts.plot(kind="barh", color="skyblue")  # Create a bar plot
    plt.title("Most Popular Tina Turner Songs")
    plt.xlabel("Song")
    plt.ylabel("Number of Times Listened")
    plt.xticks(rotation=0)  # Rotate song labels for better readability
    plt.tight_layout()  # Adjust layout to not cut off labels
    plt.show()
