"""Welcome to Reflex!."""

import reflex as rx

from lastfm import styles

# Import all the pages.
from lastfm.pages import *

# Create the app and compile it.
app = rx.App(style=styles.base_style)
# app.compile()
