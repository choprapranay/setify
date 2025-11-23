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

        # Check if credentials are set
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify credentials not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables."
            )

        try:
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
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise ValueError(
                    "Spotify authentication failed (400 Bad Request). "
                    "Please verify that SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are correct."
                ) from e
            raise

    def _normalize_song_name(self, name: str) -> str:
        """Normalize song name for exact matching"""
        name = name.lower().strip()
        # Remove common suffixes and prefixes
        name = name.replace("(live)", "").replace("[live]", "").replace("(remix)", "").replace("[remix]", "")
        name = name.replace("(feat.", "(ft.").replace("(ft.", "").replace("featuring", "ft")
        # Remove extra whitespace
        name = " ".join(name.split())
        return name

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

    def get_top_tracks(self, artist_id: str, limit: int = 50) -> List[Dict]:
        """Get artist's top tracks from Spotify"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
            headers=headers,
            params={"market": "US"},
        )

        res.raise_for_status()
        tracks = res.json().get("tracks", [])

        result = []
        for track in tracks[:limit]:
            result.append({
                "name": track["name"].strip(),
                "id": track["id"],
                "popularity": track.get("popularity", 0),
                "release_date": track.get("album", {}).get("release_date", ""),
            })
        return result

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

    def get_album_tracks(self, album_id: str) -> List[Dict]:
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
            track_id = t["id"]
            # Get full track details for popularity
            track_details = self.get_track_details(track_id)
            tracks.append({
                "name": t["name"].strip(),
                "id": track_id,
                "popularity": track_details.get("popularity", 0),
                "release_date": track_details.get("album", {}).get("release_date", ""),
            })
        return tracks

    def get_track_details(self, track_id: str) -> Dict:
        """Get full track details including popularity"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"https://api.spotify.com/v1/tracks/{track_id}",
            headers=headers
        )

        res.raise_for_status()
        return res.json()

    def get_track_popularity(self, track_id: str) -> int:
        """Legacy method for backward compatibility"""
        details = self.get_track_details(track_id)
        return details.get("popularity", 0)

    def get_new_album_tracks(self, artist_name: str) -> List[Dict]:
        """Get tracks from artist's newest album"""
        artist_id = self.get_artist_id(artist_name)
        if not artist_id:
            return []

        newest_album = self.get_newest_album(artist_id)
        if not newest_album:
            return []

        return self.get_album_tracks(newest_album["id"])

    def get_artist_track_data(self, artist_name: str) -> Dict[str, Dict]:
        """
        Get comprehensive track data for an artist:
        - Top tracks (most popular/played)
        - Newest album tracks
        Returns a dict mapping normalized song names to track data
        """
        artist_id = self.get_artist_id(artist_name)
        if not artist_id:
            return {}

        track_map = {}
        
        # Get top tracks (these are most likely to be played)
        top_tracks = self.get_top_tracks(artist_id, limit=50)
        for track in top_tracks:
            normalized = self._normalize_song_name(track["name"])
            # Keep the highest popularity if duplicate normalized names
            if normalized not in track_map or track["popularity"] > track_map[normalized].get("popularity", 0):
                track_map[normalized] = {
                    "name": track["name"],
                    "popularity": track["popularity"],
                    "id": track["id"],
                    "source": "top_tracks",
                }
        
        # Get newest album tracks
        newest_album = self.get_newest_album(artist_id)
        if newest_album:
            album_tracks = self.get_album_tracks(newest_album["id"])
            for track in album_tracks:
                normalized = self._normalize_song_name(track["name"])
                # Prefer top tracks over album tracks, but add if not present
                if normalized not in track_map:
                    track_map[normalized] = {
                        "name": track["name"],
                        "popularity": track["popularity"],
                        "id": track["id"],
                        "source": "new_album",
                    }
                elif track_map[normalized]["source"] == "new_album" and track["popularity"] > track_map[normalized].get("popularity", 0):
                    track_map[normalized]["popularity"] = track["popularity"]

        return track_map

    def match_setlist_songs_to_spotify(self, setlist_song_names: List[str], artist_name: str) -> Dict[str, Dict]:
        """
        Match setlist song names to Spotify tracks using exact matching (after normalization).
        Returns a dict mapping setlist song names to their Spotify match.
        """
        spotify_tracks = self.get_artist_track_data(artist_name)
        if not spotify_tracks:
            return {}

        matches = {}
        for setlist_name in setlist_song_names:
            # Try exact normalized match
            normalized = self._normalize_song_name(setlist_name)
            if normalized in spotify_tracks:
                matches[setlist_name] = spotify_tracks[normalized]

        return matches

