"""The now-playing page."""

import pylast
import reflex as rx

from lastfm.config import USER_NAME
from lastfm.templates import template
from lastfm.tools.get_lyrics import get_lyrics
from lastfm.tools.mylast import lastfm_network


def _convert_ms_to_hms(milliseconds: float | str) -> str:
    ms = float(milliseconds)
    seconds = int((ms / 1000) % 60)
    minutes = int(ms / (1000 * 60))
    time_format = f"{minutes} min {seconds} sec"
    return time_format


class NowPlaying:
    def __init__(self) -> None:
        self.now_playing = "Nothing is playing"

    def reset(self) -> None:
        self.now_playing = ""

    def find_now_playing(self) -> pylast.Track:
        self.reset()
        try:
            now_playing = lastfm_network.get_user(USER_NAME).get_now_playing()
            if now_playing is not None:
                return now_playing
        except (
            pylast.MalformedResponseError,
            pylast.NetworkError,
            pylast.WSError,
        ) as e:
            print(f"Error: {e}", "error")
        else:
            return "I'm not listening to music atm :/"


class NowPlayingState(rx.State):
    """The app state."""

    now_playing = ""
    song = ""
    album_cover = ""
    playcount = ""
    artist = ""
    artist_playcount = ""
    artist_top_albums = ""
    artist_top_tracs = ""
    artist_similar = ""
    album = ""
    album_playcount = ""
    duration = ""
    info = ""
    lyrics = ""
    processing = False
    complete = False
    playing = False

    def get_nowplaying(self) -> None:
        """Get the currently playing audio."""
        self.processing, self.complete = True, False
        yield
        response = NowPlaying().find_now_playing()
        self.now_playing = str(response)
        match response:
            case "I'm not listening to music atm :/":
                self.playing = False
            case _:
                self.playing = True
                self.song = response.get_name()
                self.album_cover = response.get_cover_image()
                self.playcount = response.get_userplaycount()
                artist = response.get_artist()
                artist.username = USER_NAME
                self.artist = artist.get_name()
                self.artist_playcount = artist.get_userplaycount()
                # self.artist_top_tracs = str(artist.get_top_tracks(limit=5)[0])
                # self.artist_top_albums = str(artist.get_top_albums(limit=5))
                self.artist_top_tracs = (
                    '"'
                    + '", "'.join(
                        [a.item.get_name() for a in artist.get_top_tracks(limit=5)]
                    )
                    + '"'
                )
                self.artist_top_albums = (
                    '"'
                    + '", "'.join(
                        [a.item.get_name() for a in artist.get_top_albums(limit=5)]
                    )
                    + '"'
                )
                self.artist_similar = (
                    '"'
                    + '", "'.join(
                        [a.item.get_name() for a in artist.get_similar(limit=5)]
                    )
                    + '"'
                )
                self.album = response.get_album().get_name()
                self.album_playcount = response.get_album().get_userplaycount()
                self.duration = _convert_ms_to_hms(response.get_duration())
                self.info = response.get_mbid()
                self.lyrics = get_lyrics(self.artist, self.song)
        self.processing, self.complete = False, True


@template(route="/now-playing", title="Now Playing")
def now_playing() -> rx.Component:
    """Run the component for the now-playing page.

    Returns
    -------
    rx.Component
        The UI for the now-playing page.
    """
    list_item_color = "purple"
    return rx.vstack(
        rx.heading("Now Playing", font_size="3em"),
        rx.button(
            "What are you listening to, Eirik?",
            on_click=NowPlayingState.get_nowplaying,
            is_loading=NowPlayingState.processing,
            width="100%",
        ),
        rx.cond(
            NowPlayingState.complete,
            rx.chakra.heading(NowPlayingState.now_playing, color="purple", size="md"),
        ),
        rx.cond(
            NowPlayingState.playing,
            rx.chakra.hstack(
                rx.image(src=NowPlayingState.album_cover),
                # https://reflex.dev/docs/library/chakra/media/icon/
                rx.chakra.list(
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="time", color=list_item_color),
                        " It is " + NowPlayingState.duration + " long",
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="repeat", color=list_item_color),
                        " I have listened to this track "
                        + NowPlayingState.playcount
                        + " times :)",
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="repeat", color=list_item_color),
                        " I have listened to the album "
                        + NowPlayingState.album
                        + " "
                        + NowPlayingState.album_playcount
                        + " times :)",
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="repeat", color=list_item_color),
                        " I have listened to "
                        + NowPlayingState.artist
                        + " "
                        + NowPlayingState.artist_playcount
                        + " times :)",
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="star", color=list_item_color),
                        " Their top 5 songs are " + NowPlayingState.artist_top_tracs,
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="sun", color=list_item_color),
                        " Their top 5 albums are " + NowPlayingState.artist_top_albums,
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="view", color=list_item_color),
                        " If you enjoy listening to "
                        + NowPlayingState.artist
                        + ", here are five similar artists! "
                        + NowPlayingState.artist_similar,
                    ),
                    rx.chakra.list_item(
                        rx.chakra.icon(tag="lock", color=list_item_color),
                        " It's MusicBrainz ID is " + NowPlayingState.info,
                    ),
                    width="100%",
                ),
                spacing="10%",
                width="80%",
            ),
        ),
        rx.cond(
            NowPlayingState.playing,
            rx.vstack(
                rx.markdown("## Lyrics"),
                rx.markdown(
                    "I searched on [Genius](https://genius.com/) for the lyrics of "
                    + f'"{NowPlayingState.artist}" (artist) and "{NowPlayingState.song}" (song), '
                    + "and this is what I found:"
                ),
                rx.box(
                    rx.code_block(
                        NowPlayingState.lyrics,
                        language="markup",
                        copy_button=True,
                        wrap_long_lines=True,
                        show_line_numbers=True,
                    ),
                    height="50vh",
                    width="80%",
                    overflow_y="auto",
                ),
            ),
        ),
    )
