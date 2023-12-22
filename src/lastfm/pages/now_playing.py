"""The now-playing page."""

import pylast
import reflex as rx

from lastfm.config import USER_NAME
from lastfm.templates import template
from lastfm.tools.mylast import lastfm_network


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
            output(f"Error: {e}", "error")
        else:
            return "I'm not listening to music atm :/"


class State(rx.State):
    """The app state."""

    now_playing = ""
    processing = False
    complete = False

    def get_nowplaying(self):
        """Get the image from the prompt."""
        self.processing, self.complete = True, False
        yield
        response = NowPlaying().find_now_playing()
        self.now_playing = str(response)
        self.processing, self.complete = False, True


@template(route="/now-playing", title="Now Playing")
def now_playing() -> rx.Component:
    """The now-playing page.

    Returns
    -------
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
            rx.text(State.now_playing),
        ),
    )
