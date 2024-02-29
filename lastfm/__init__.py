"""Initialize the app."""

from importlib_metadata import version

from lastfm import config

__version__ = version(__package__)

__all__ = ["config"]
