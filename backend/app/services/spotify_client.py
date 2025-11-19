import time
import requests
from typing import List, Dict, Optional
from backend.app.core.config import get_settings

class SpotifyService:
    def __init__(self):
        setting = get_settings()
        self.client_id = setting.spotify_client_id
        self.client_secret = setting.spotify_client_secret
        self.token_cache = {"access_token": None, "expires_at": 0}

    def _get_access_token(self) -> str:
        if (
            self.token_cache["access_token"]
            and time.time() < self.token_cache["expires_at"]
        ):
            return self.token_cache["access_token"]

        auth_res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
        )

        auth_res.raise_for_status()
        data = auth_res.json()
        access_token = data["access_token"]

        self.token_cache = {
            "access_token": access_token,
            "expires_at": time.time() + int(data["expires_in"]) - 30
        }

        return access_token

    def get_artist_id(self, artist_name: str) -> Optional[str]:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": artist_name, "type": "artist", "limit": 1},
        )

        res.raise_for_status()
        data = res.json()

        items = data.get("artists", {}).get("items", [])
        if not items:
            return None

        return items[0]["id"]

    def get_newest_album(self, artist_id: str) -> Optional[dict]:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/albums",
            headers=headers,
            params={
                "include_groups": "album",
                "market": "US",
                "limit": 10
            },
        )

        res.raise_for_status()
        albums = res.json().get("items", [])
        if not albums:
            return None

        albums.sort(key=lambda x: x["release_date"], reverse=True)
        return albums[0]

    def get_album_tracks(self, album_id: str) -> List[str]:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"https://api.spotify.com/v1/albums/{album_id}/tracks",
            headers=headers,
            params={"market": "US", "limit": 50},
        )

        res.raise_for_status()
        items = res.json().get("items", [])

        tracks = []
        for t in items:
            tracks.append({
                "name": t["name"].strip(),
                "id": t["id"],
                "popularity": self.get_track_popularity(t["id"])
            })
        return tracks


    def get_new_album_tracks(self, artist_name: str) -> List[str]:
        artist_id = self.get_artist_id(artist_name)
        if not artist_id:
            return []

        newest_album = self.get_newest_album(artist_id)
        if not newest_album:
            return []

        return self.get_album_tracks(newest_album["id"])

    def get_track_popularity(self, track_id: str) -> int:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"https://api.spotify.com/v1/tracks/{track_id}",
            headers=headers
        )

        res.raise_for_status()
        return res.json().get("popularity", 0)

