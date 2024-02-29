import sys

from lastfm.config import USER_NAME
from lastfm.tools.mylast import lastfm_network

# Prints a list of you last loved tracks on Last.fm.
# Optional parameter: number of tracks
# Prerequisites: mylast.py, pyLast


number = int(sys.argv[1]) if len(sys.argv) > 1 else 20
last_loved_tracks = lastfm_network.get_user(USER_NAME).get_loved_tracks(limit=number)

for i, track in enumerate(last_loved_tracks):
    print(str(i + 1) + ")\t" + str(track[0]))

# End of file
