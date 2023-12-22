"""The now-playing page."""

import reflex as rx

from lastfm.templates import template
from lastfm.tools import np


class State(rx.State):
    """The app state."""

    now_playing = ""
    processing = False
    complete = False

    def get_nowplaying(self):
        """Get the image from the prompt."""
        # if self.prompt == "":
        #     return rx.window_alert("Prompt Empty")

        self.processing, self.complete = True, False
        yield
        response = np.NowPlaying().find_now_playing()
        self.now_playing = str(response)
        # self.now_playing = f"{response.artist} – {response.title}"
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
        rx.text("Welcome to Reflex!"),
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
