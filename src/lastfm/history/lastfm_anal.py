import re
import string
import plastik

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
from lastfm.config import TIME_ZONE
from matplotlib import cm

# define the fonts to use for plots
family = "DejaVu Sans"
title_font = fm.FontProperties(
    family=family, style="normal", size=20, weight="normal", stretch="normal"
)
label_font = fm.FontProperties(
    family=family, style="normal", size=16, weight="normal", stretch="normal"
)
ticks_font = fm.FontProperties(
    family=family, style="normal", size=12, weight="normal", stretch="normal"
)
ticks_font_h = fm.FontProperties(
    family=family, style="normal", size=10.5, weight="normal", stretch="normal"
)


def get_colors(cmap, n, start=0.0, stop=1.0, alpha=1.0, reverse=False):
    """Return n-length list of rgba colors from the passed colormap name and alpha,
    limit extent by start/stop values and reverse list order if flag is true
    """
    colors = [cm.get_cmap(cmap)(x) for x in np.linspace(start, stop, n)]
    colors = [(r, g, b, alpha) for r, g, b, _ in colors]
    return list(reversed(colors)) if reverse else colors


artists_most = pd.read_csv("data/lastfm_top_artists.csv", encoding="utf-8")
artists_most = artists_most.set_index("artist")["play_count"].head(25)
# print(artists_most.head())


def plot_top_artists() -> None:
    ax = artists_most.plot(
        kind="bar",
        figsize=[11, 7],
        width=0.8,
        alpha=0.7,
        color="#339933",
        edgecolor=None,
        zorder=2,
    )

    ax.yaxis.grid(True)
    ax.set_xticklabels(
        artists_most.index,
        rotation=45,
        rotation_mode="anchor",
        ha="right",
        fontproperties=ticks_font,
    )
    for label in ax.get_yticklabels():
        label.set_fontproperties(ticks_font)

    ax.set_title("Artists I have played the most", fontproperties=title_font)
    ax.set_xlabel("", fontproperties=label_font)
    ax.set_ylabel("Number of plays", fontproperties=label_font)

    plt.savefig("images/lastfm-artists-played-most.png", dpi=96, bbox_inches="tight")
    plt.show()


def make_label(row, maxlength=30, suffix="..."):
    artist = row["artist"]
    track = row["track"]
    if len(track) > maxlength:
        track = f"{track[:maxlength - len(suffix)]}{suffix}"
    return f"{artist}\n{track}"


def plot_top_tracks() -> None:
    tracks_most = pd.read_csv("data/lastfm_top_tracks.csv", encoding="utf-8")
    index = tracks_most.apply(make_label, axis="columns")
    tracks_most = tracks_most.set_index(index).drop(
        labels=["artist", "track"], axis="columns"
    )
    tracks_most = tracks_most["play_count"].head(20)
    print(tracks_most.head())

    ax = tracks_most.sort_values().plot(
        kind="barh",
        figsize=[6, 10],
        width=0.8,
        alpha=0.6,
        color="#003399",
        edgecolor=None,
        zorder=2,
    )
    ax.xaxis.grid(True)
    for label in ax.get_xticklabels():
        label.set_fontproperties(ticks_font_h)
    for label in ax.get_yticklabels():
        label.set_fontproperties(ticks_font_h)
    ax.set_xlabel("Number of plays", fontproperties=label_font)
    ax.set_ylabel("", fontproperties=label_font)
    ax.set_title("Songs I have played the most", fontproperties=title_font, y=1.005)

    plt.savefig("images/lastfm-tracks-played-most-h.png", dpi=96, bbox_inches="tight")
    plt.show()


def make_label(row, maxlength=25, suffix="..."):
    artist = row["artist"]
    track = row["album"]
    if len(track) > maxlength:
        track = f"{track[:maxlength - len(suffix)]}{suffix}"
    return f"{artist}\n{track}"


def plot_top_albums() -> None:
    albums_most = pd.read_csv("data/lastfm_top_albums.csv", encoding="utf-8")
    index = albums_most.apply(make_label, axis="columns")
    albums_most = albums_most.set_index(index).drop(
        labels=["artist", "album"], axis="columns"
    )
    albums_most = albums_most["play_count"].head(30)
    print(albums_most.head())

    ax = albums_most.sort_values().plot(
        kind="barh",
        figsize=[6.5, 15],
        width=0.8,
        alpha=0.6,
        color="#990066",
        edgecolor=None,
        zorder=2,
    )
    ax.xaxis.grid(True)
    for label in ax.get_xticklabels():
        label.set_fontproperties(ticks_font_h)
    for label in ax.get_yticklabels():
        label.set_fontproperties(ticks_font_h)
    ax.set_xlabel("Number of plays", fontproperties=label_font)
    ax.set_ylabel("", fontproperties=label_font)
    ax.set_title("Albums I have played the most", fontproperties=title_font, y=1.005)

    plt.savefig("images/lastfm-albums-played-most-h.png", dpi=96, bbox_inches="tight")
    plt.show()


# read the all-time scrobbles data set
scrobbles = pd.read_csv("data/lastfm_scrobbles.csv", encoding="utf-8")
scrobbles = scrobbles.drop("timestamp", axis=1)
# print(f"{len(scrobbles):,} total scrobbles")
# print("{:,} total artists".format(len(scrobbles["artist"].unique())))

# convert to datetime
scrobbles["timestamp"] = pd.to_datetime(scrobbles["datetime"])


# functions to convert UTC to Pacific time zone and extract date/time elements
def convert_tz(x):
    return x.to_pydatetime().replace(tzinfo=pytz.utc).astimezone(TIME_ZONE)


def get_year(x):
    return convert_tz(x).year


def get_month(x):
    return f"{convert_tz(x).year}-{convert_tz(x).month:02}"  # inefficient


def get_day(x):
    return convert_tz(x).day


def get_hour(x):
    return convert_tz(x).hour


def get_day_of_week(x):
    return convert_tz(x).weekday()


# parse out date and time elements as my time
scrobbles["year"] = scrobbles["timestamp"].map(get_year)
scrobbles["month"] = scrobbles["timestamp"].map(get_month)
scrobbles["day"] = scrobbles["timestamp"].map(get_day)
scrobbles["hour"] = scrobbles["timestamp"].map(get_hour)
scrobbles["dow"] = scrobbles["timestamp"].map(get_day_of_week)
scrobbles = scrobbles.drop(labels=["datetime"], axis=1)

# drop rows with 01-01-1970 as timestamp
scrobbles = scrobbles[scrobbles["year"] > 1970]
# print(scrobbles.head())


def plot_scrobbles_per_year() -> None:
    year_counts = scrobbles["year"].value_counts().sort_index()
    ax = year_counts.plot(
        kind="line",
        figsize=[10, 5],
        linewidth=4,
        alpha=1,
        marker="o",
        color="#6684c1",
        markeredgecolor="#6684c1",
        markerfacecolor="w",
        markersize=8,
        markeredgewidth=2,
    )

    ax.set_xlim((year_counts.index[0], year_counts.index[-1]))

    ax.yaxis.grid(True)
    ax.xaxis.grid(True)
    ax.set_ylim(0, 70000)
    ax.set_xticks(year_counts.index)
    ax.set_ylabel("Number of plays", fontproperties=label_font)
    ax.set_xlabel("", fontproperties=label_font)
    ax.set_title("Number of songs played per year", fontproperties=title_font)

    plt.savefig("images/lastfm-scrobbles-per-year.png", dpi=96, bbox_inches="tight")
    plt.show()


def plot_scrobbles_per_month() -> None:
    # get all the scrobbles from 2009-present
    min_year = 2009
    scrobbles_10 = scrobbles[scrobbles["year"] >= min_year]
    max_year = max(scrobbles_10["year"])

    # count number of scrobbles in each month
    month_counts = scrobbles_10["month"].value_counts().sort_index()

    # not every month necessarily has a scrobble, so fill in missing months with zero
    # counts
    date_range = pd.date_range(
        start=min(scrobbles_10["timestamp"]),
        end=max(scrobbles_10["timestamp"]),
        freq="D",
    )
    months_range = date_range.map(lambda x: str(x.date())[:-3])
    index = np.unique(months_range)
    month_counts = month_counts.reindex(index, fill_value=0)

    ax = month_counts.plot(
        kind="line", figsize=[12, 5], linewidth=4, alpha=0.6, color="#003399"
    )

    xlabels = month_counts.iloc[range(0, len(month_counts), 12)].index
    xlabels = [x if x in xlabels else "" for x in month_counts.index]
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=40, rotation_mode="anchor", ha="right")

    ax.set_xlim((0, len(month_counts) - 1))

    ax.yaxis.grid(True)
    ax.set_ylim((0, 8000))
    ax.set_ylabel("Number of plays", fontproperties=label_font)
    ax.set_xlabel("", fontproperties=label_font)
    ax.set_title(
        f"Number of songs played per month, {min_year}-{max_year}",
        fontproperties=title_font,
    )

    plt.savefig("images/lastfm-scrobbles-per-month.png", dpi=96, bbox_inches="tight")
    plt.show()


def plot_scrobbles_per_weekday() -> None:
    # get the play count sum by day of the week
    dow_counts = scrobbles["dow"].value_counts().sort_index()
    dow_counts.index = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    ax = dow_counts.plot(
        kind="bar",
        figsize=[6, 5],
        width=0.7,
        alpha=0.6,
        color="#003399",
        edgecolor=None,
        zorder=2,
    )

    ax.yaxis.grid(True)
    ax.set_xticklabels(
        dow_counts.index,
        rotation=35,
        rotation_mode="anchor",
        ha="right",
        fontproperties=ticks_font,
    )
    for label in ax.get_yticklabels():
        label.set_fontproperties(ticks_font)

    ax.set_ylim((0, 45000))
    ax.set_title("Songs played per day of the week", fontproperties=title_font)
    ax.set_xlabel("", fontproperties=label_font)
    ax.set_ylabel("Number of plays", fontproperties=label_font)

    plt.savefig("images/lastfm-scrobbles-per-weekday.png", dpi=96, bbox_inches="tight")
    plt.show()


def plot_scrobbles_per_hour() -> None:
    hour_counts = scrobbles["hour"].value_counts().sort_index()
    ax = hour_counts.plot(
        kind="line",
        figsize=[10, 5],
        linewidth=4,
        alpha=1,
        marker="o",
        color="#6684c1",
        markeredgecolor="#6684c1",
        markerfacecolor="w",
        markersize=8,
        markeredgewidth=2,
    )

    xlabels = hour_counts.index.map(lambda x: f"{x:02}:00")
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=45, rotation_mode="anchor", ha="right")

    ax.set_xlim((hour_counts.index[0], hour_counts.index[-1]))

    ax.yaxis.grid(True)
    ax.set_ylim((0, 20000))
    ax.set_ylabel("Number of plays", fontproperties=label_font)
    ax.set_xlabel("", fontproperties=label_font)
    ax.set_title(
        "Number of songs played per hour of the day", fontproperties=title_font
    )

    plt.savefig("images/lastfm-scrobbles-per-hour.png", dpi=96, bbox_inches="tight")
    plt.show()


def plot_scrobbles_per_weekday_and_hour() -> None:
    # get the play counts by hour of day and day of week
    weekday_hour_counts = scrobbles.groupby(["dow", "hour"]).count()["track"]
    hour_numbers = weekday_hour_counts.index.levels[1]
    day_numbers = weekday_hour_counts.index.levels[0]
    day_names = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    # get one color per day of week
    colors = get_colors("nipy_spectral_r", n=len(day_numbers), start=0.1, stop=0.95)

    fig, ax = plt.subplots(figsize=[10, 6])
    lines = []
    for day, c in zip(day_numbers, colors):
        ax = weekday_hour_counts[day].plot(kind="line", linewidth=4, alpha=0.6, c=c)
        lines.append(day_names[day])

    xlabels = hour_numbers.map(lambda x: f"{x:02}:00")
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=45, rotation_mode="anchor", ha="right")

    ax.set_xlim((hour_numbers[0], hour_numbers[-1]))

    ax.yaxis.grid(True)
    ax.set_ylim([0, 3500])
    ax.set_ylabel("Number of plays", fontproperties=label_font)
    ax.set_xlabel("", fontproperties=label_font)
    ax.set_title(
        "Number of songs played, by day of week and hour of day",
        fontproperties=title_font,
    )
    ax.legend(lines, loc="upper right", bbox_to_anchor=(1.23, 1.017))

    plt.savefig("images/lastfm-scrobbles-days-hours.png", dpi=96, bbox_inches="tight")
    plt.show()


def top_artist_in_year(year: int = 2015) -> None:
    scrobbles_year = scrobbles[scrobbles["year"].isin([year])]
    len(scrobbles_year)

    # what artists did i play the most that year?
    artists_year = scrobbles_year["artist"].value_counts()
    artists_year = (
        pd.DataFrame(artists_year)
        .reset_index()
        .rename(columns={"artist": "play count", "index": "artist"})
    )
    artists_year.index = [n + 1 for n in artists_year.index]
    artists_year.head(10)


def top_tracks_in_year(year: int = 2015) -> None:
    scrobbles_year = scrobbles[scrobbles["year"].isin([year])]
    # what tracks did i play the most that year?
    tracks_year = (
        scrobbles_year.groupby(["artist", "track"])
        .count()
        .sort_values("timestamp", ascending=False)
    )
    tracks_year = tracks_year.reset_index().rename(columns={"timestamp": "play count"})[
        ["artist", "track", "play count"]
    ]
    tracks_year.index = [n + 1 for n in tracks_year.index]
    tracks_year.head(10)


def top_albums_in_year(year: int = 2015) -> None:
    scrobbles_year = scrobbles[scrobbles["year"].isin([year])]
    # what albums did i play the most that year?
    albums_year = (
        scrobbles_year.groupby(["artist", "album"])
        .count()
        .sort_values("timestamp", ascending=False)
    )
    albums_year = albums_year.reset_index().rename(columns={"timestamp": "play count"})[
        ["artist", "album", "play count"]
    ]
    albums_year.index = [n + 1 for n in albums_year.index]

    # remove text in parentheses or brackets
    regex = re.compile("\\(.*\\)|\\[.*]")
    albums_year["album"] = albums_year["album"].map(lambda x: regex.sub("", x))
    albums_year.head(10)


def top_in_month() -> None:
    scrobbles_month = scrobbles[scrobbles["month"].isin(["2014-02"])]
    len(scrobbles_month)

    # what artists did i play the most that month?
    artists_month = scrobbles_month["artist"].value_counts()
    artists_month = (
        pd.DataFrame(artists_month)
        .reset_index()
        .rename(columns={"artist": "play count", "index": "artist"})
    )
    artists_month.index = [n + 1 for n in artists_month.index]
    artists_month.head(10)

    tracks_played_in_given_month(scrobbles_month, "track")
    tracks_played_in_given_month(scrobbles_month, "album")


# TODO Rename this here and in `top_in_month`
def tracks_played_in_given_month(scrobbles_month, arg1):
    # what tracks did i play the most that month?
    tracks_month = (
        scrobbles_month.groupby(["artist", arg1])
        .count()
        .sort_values("timestamp", ascending=False)
    )
    tracks_month = tracks_month.reset_index().rename(
        columns={"timestamp": "play count"}
    )[["artist", arg1, "play count"]]
    tracks_month.index = [n + 1 for n in tracks_month.index]
    tracks_month.head(10)


def last_five_times_i_played() -> None:
    # when were the last 5 times I played something by My Bloody Valentine?
    print(scrobbles[scrobbles["artist"].str.contains("Metallica")].head())


def plot_cumulative_play_count(since: int = 2005, n: int = 10) -> None:
    # get the cumulative play counts since 2009 for the top n most listened-to artists
    # print(scrobbles)
    # scrobbles = scrobbles[scrobbles["year"] > 1970]
    # scrobbles = scrobbles[scrobbles["year"] >= since]
    # scrobb = scrobbles[scrobbles["year"] > since]
    plays = scrobbles[scrobbles["artist"].isin(artists_most.head(n).index)]
    plays = plays[plays["year"] >= since]
    plays = (
        plays.groupby(["artist", "year"]).count().groupby(level=[0]).cumsum()["track"]
    )

    # make sure we have each year represented for each artist, even if they got no plays
    # that year
    plays = plays.unstack().T.fillna(method="ffill").T.stack()
    top_artists = plays.index.levels[0]

    # get one color per artist
    colors = get_colors("Dark2", n)
    colors = plastik.colors.create_colorlist("cmc.batlow", n)

    fig, ax = plt.subplots(figsize=[8, 6])
    lines = []
    for artist, c in zip(top_artists, colors):
        ax = plays[artist].plot(kind="line", linewidth=4, alpha=0.6, marker="o")
        lines.append(artist)

    # ax.set_xlim(
    #     (plays.index.get_level_values(1).min(), plays.index.get_level_values(1).max())
    # )

    ax.yaxis.grid(True)
    ax.set_xticklabels(
        plays.index.levels[1], rotation=0, rotation_mode="anchor", ha="center"
    )
    ax.set_ylabel("Cumulative number of plays", fontproperties=label_font)
    ax.set_xlabel("Year", fontproperties=label_font)
    ax.set_title(
        "Cumulative number of plays per artist over time", fontproperties=title_font
    )
    ax.legend(lines, loc="upper right", bbox_to_anchor=(1.33, 1.016))

    plt.tight_layout()
    plt.savefig(
        "images/lastfm-scrobbles-top-artists-years.png", dpi=96, bbox_inches="tight"
    )
    plt.show()


def plot_first_letter_count() -> None:
    # remove 'The ' and 'A ' preceding artist names, get unique set of names, then get
    # first letter frequency
    artists_clean = scrobbles["artist"].str.replace("The ", "").str.replace("A ", "")
    first_letters = (
        pd.Series(artists_clean.unique()).map(lambda x: x.upper()[0]).value_counts()
    )
    first_letters = first_letters[list(string.ascii_uppercase)]

    # plot the frequency of artist names that begin with each letter
    ax = first_letters.plot(
        kind="bar",
        figsize=[10, 6],
        width=0.8,
        alpha=0.6,
        color="#339933",
        edgecolor=None,
        zorder=2,
    )
    ax.yaxis.grid(True)
    ax.set_xticklabels(
        first_letters.index,
        rotation=0,
        rotation_mode="anchor",
        ha="center",
        fontproperties=ticks_font,
    )

    ax.set_title(
        "Number of artist names that begin with each letter", fontproperties=title_font
    )
    ax.set_xlabel("First letter in name", fontproperties=label_font)
    ax.set_ylabel("Number of unique artists", fontproperties=label_font)

    plt.savefig(
        "images/lastfm-artists-first-letter-count.png", dpi=96, bbox_inches="tight"
    )
    plt.show()


def artist_starting_with_letter(letter: str = "X") -> None:
    # which artist names begin with the letter 'X'?
    artists_clean = scrobbles["artist"].str.replace("The ", "").str.replace("A ", "")
    print(
        str(
            list(
                pd.Series(
                    artists_clean[
                        artists_clean.str.upper().str.startswith(letter)
                    ].unique()
                )
            )
        )
    )


def most_common_words_in_artist_starting_with_letter(letter: str = "M") -> None:
    # what are the most common first words in artist names that begin with 'M'?
    artists_clean = scrobbles["artist"].str.replace("The ", "").str.replace("A ", "")
    artists_m = pd.Series(
        artists_clean[artists_clean.str.upper().str.startswith(letter)].unique()
    )
    artists_m.map(lambda x: x.split()[0]).value_counts().head(15)


def most_common_first_word_in_artist_name() -> None:
    # what are the most common first words in all the artist names?
    pd.Series(scrobbles["artist"].unique()).map(
        lambda x: x.split()[0].lower()
    ).value_counts().head(15)


def most_common_word_in_artist_name() -> None:
    # what are the most common words in all the artist names, anywhere in the name?
    artists_clean = scrobbles["artist"].str.replace("The ", "").str.replace("A ", "")
    word_list: list[str] = []
    stop_list = [
        "&",
        "the",
        "and",
        "of",
        "a",
        "in",
        "for",
        "la",
        "los",
        "el",
        "de",
        "y",
    ]
    for artist in artists_clean.unique():
        word_list.extend(word.lower() for word in artist.split())
    word_list = [word for word in word_list if word not in stop_list]
    pd.Series(word_list).value_counts().head(15)


def longest_artist_name() -> None:
    # what is the longest artist name?
    artists_clean = scrobbles["artist"].str.replace("The ", "").str.replace("A ", "")
    print(f'"{max(artists_clean, key=len)}"')


def length_distribution() -> None:
    # what is the distribution of lengths of artist names (up to n number of
    # characters)?
    artists_clean = scrobbles["artist"].str.replace("The ", "").str.replace("A ", "")
    n = 50
    name_lengths = pd.Series([len(artist) for artist in artists_clean.unique()])
    name_lengths = name_lengths.value_counts().sort_index()
    name_lengths = name_lengths.iloc[: n + 1].reindex(range(n + 1), fill_value=0)

    ax = name_lengths.plot(
        kind="bar",
        figsize=(10, 6),
        alpha=0.6,
        width=1,
        color="#990066",
        edgecolor="#990066",
        zorder=2,
    )

    xlabels = [x if x % 10 == 0 else "" for x in name_lengths.index]
    ax.set_xticklabels(
        xlabels,
        rotation=0,
        rotation_mode="anchor",
        ha="center",
        fontproperties=ticks_font,
    )
    ax.yaxis.grid(True)
    ax.set_xlim((0, n))

    ax.set_title("Frequency of artist name length", fontproperties=title_font)
    ax.set_xlabel("Number of characters in artist name", fontproperties=label_font)
    ax.set_ylabel("Number of artists", fontproperties=label_font)

    plt.savefig("images/lastfm-artists-name-length.png", dpi=96, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    # plot_scrobbles_per_weekday_and_hour()
    plot_cumulative_play_count(2019, n=50)
    # plot_top_albums()
