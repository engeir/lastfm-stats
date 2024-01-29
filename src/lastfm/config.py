"""Set global configuration values."""

import subprocess

import pylast
import pendulum

API_KEY = subprocess.check_output(["pass", "Lastfm/API_KEY"]).strip().decode()
API_SECRET = subprocess.check_output(["pass", "Lastfm/API_SECRET"]).strip().decode()
USER_NAME = subprocess.check_output(["pass", "Lastfm/Username"]).strip().decode()
PASSWORD = subprocess.check_output(["pass", "Lastfm/Password"]).strip().decode()
PASSWORD_HASH = pylast.md5(PASSWORD)
GENIUS_TOKEN = subprocess.check_output(["pass", "Genius/Client-access-token"]).strip().decode()

TIME_ZONE = pendulum.timezone("Europe/Oslo")
