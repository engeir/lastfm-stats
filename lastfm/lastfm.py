"""Welcome to Reflex!"""

import reflex as rx

# Import all the pages.
from lastfm.pages import *

# Create the app and compile it.
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="purple",
    )
    # style=styles.base_style
)
# app.compile()
