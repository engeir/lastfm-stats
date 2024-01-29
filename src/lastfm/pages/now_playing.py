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


class State(rx.State):
    """The app state."""

    now_playing = ""
    song = ""
    album_cover = ""
    playcount = ""
    artist = ""
    artist_playcount = ""
    duration = ""
    info = ""
    lyrics = ""
    processing = False
    complete = False
    playing = False

    def get_nowplaying(self):
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
                self.artist = response.get_artist().get_name()
                self.artist_playcount = response.get_artist().get_userplaycount()
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
    return rx.vstack(
        rx.heading("Now Playing", font_size="3em"),
        rx.button(
            "What are you listening to, Eirik?",
            on_click=State.get_nowplaying,
            is_loading=State.processing,
            width="100%",
        ),
        rx.cond(
            State.complete,
            rx.heading(State.now_playing, color="purple", size="md"),
        ),
        rx.cond(
            State.playing,
            rx.hstack(
                rx.image(src=State.album_cover),
                # https://reflex.dev/docs/library/chakra/media/icon/
                rx.list(
                    rx.list_item(
                        rx.icon(tag="repeat", color="black"),
                        " I have listened to this track "
                        + State.playcount
                        + " times :)",
                    ),
                    rx.list_item(
                        rx.icon(tag="repeat", color="black"),
                        " I have listened to "
                        + State.artist
                        + " "
                        + State.artist_playcount
                        + " times :)",
                    ),
                    rx.list_item(
                        rx.icon(tag="time", color="black"),
                        " It is " + State.duration + " long",
                    ),
                ),
                spacing="10%",
            ),
        ),
        rx.cond(
            State.playing,
            rx.vstack(
                rx.markdown("## Lyrics"),
                rx.markdown(
                    "I searched on [Genius](https://genius.com/) for the lyrics of "
                    + f'"{State.artist}" (artist) and "{State.song}" (song), '
                    + "and this is what I found:"
                ),
                rx.code_block(
                    State.lyrics,
                    language="markup",
                    copy_button=True,
                    wrap_long_lines=True,
                    show_line_numbers=True,
                ),
            ),
        ),
    )
