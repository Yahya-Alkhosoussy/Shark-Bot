from os import getenv

import spotipy
import yt_dlp
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
    )
)

YDL_OPTS = {"format": "bestaudio", "quiet": True, "default_search": "ytsearch1"}


def resolve_spotify_track(url: str) -> list[str]:
    """Spotify URL -> 'Artist - Title' search string."""
    track = None
    if "/track/" in url:
        track = sp.track(url)
        if track is None:
            raise ValueError(f"Unsupported Spotify URL: {url}")
        to_return = [f"{track['artists'][0]['name']} - {track['name']}"]
        return to_return
    elif "/album/" in url:
        track = sp.album_tracks(url)
        if track is not None:
            items = track["items"]
            to_return = [f"{t['artists'][0]['name']} - {t['name']}" for t in items]
            return to_return
        else:
            raise ValueError(f"Unsupported Spotify URL: {url}")
    elif "/playlist/" in url:
        result = sp.playlist_items(url)
        if result is None:
            raise ValueError(f"Unsupported Spotify URL: {url}")
        track = []
        while result:
            for item in result["items"]:
                t = item.get("track")
                if t:
                    tracks.append(f"{t['artists'][0]['name']} - {t['name']}")
            result = sp.next(result) if result["next"] else None
        return tracks
    else:
        raise ValueError(f"Unsupported Spotify URL: {url}")


def get_stream_url(query: str) -> str:
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:  # type: ignore
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info["url"]  # type: ignore


if __name__ == "__main__":
    tracks = resolve_spotify_track("https://open.spotify.com/album/5P7YyqqjHuq7mSLqIY06jE?si=FQNv_8UPTOeW3k85tKCg4A")
    urls = []
    for track in tracks:
        if track != "Song not found":
            urls.append(get_stream_url(track))

    print(tracks)
    print(urls)
