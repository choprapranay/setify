from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from backend.app.core.config import get_settings
from backend.app.entities.models import Artist, Setlist, SetlistMeta, SongAppearance


class SetlistFMError(RuntimeError):
    """Base error raised for Setlist.fm client failures."""


class SetlistFMCredentialsError(SetlistFMError):
    """Raised when Setlist.fm rejects requests because of missing/invalid credentials."""


load_dotenv()

# Helper Function
def _parse_event_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

class SetlistFMClient:
    """ Responsible for talking to the Setlist.fm API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.setlistfm_base.rstrip("/")
        self._headers = {
            "x-api-key": settings.setlistfm_api_key,
            "Accept": "application/json",
        }
        self._timeout = httpx.Timeout(30.0)

    async def _request(self, client: httpx.AsyncClient, path: str, params: Dict) -> Dict:
        if not self._headers.get("x-api-key"):
            raise SetlistFMCredentialsError(
                "Setlist.fm API key is missing. Set the SETLISTFM_API_KEY environment variable."
            )

        response = await client.get(f"{self._base}{path}", params=params, headers=self._headers)
        if response.status_code == 404:
            return {}
        if response.status_code == 429:
            retry = int(response.headers.get("Retry-After", "1"))
            await asyncio.sleep(min(retry, 5))
            response = await client.get(f"{self._base}{path}", params=params, headers=self._headers)
        if response.status_code in {401, 403}:
            raise SetlistFMCredentialsError(
                "Setlist.fm rejected the request (status %s). Verify SETLISTFM_API_KEY is correct." % response.status_code
            )
        response.raise_for_status()
        return response.json()

    async def search_artist(self, name: str) -> Optional[Artist]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            data = await self._request(client, "/search/artists", {"artistName": name, "p": 1})
        artists = data.get("artist", []) if data else []
        if not artists:
            return None
        exact = next((a for a in artists if a.get("name", "").lower() == name.lower()), None)
        chosen = exact or artists[0]
        if not chosen.get("mbid") or not chosen.get("name"):
            return None
        return Artist(name=chosen["name"], mbid=chosen["mbid"])

    async def fetch_setlists(self, mbid: str, max_pages: int = 5) -> Tuple[List[Setlist], SetlistMeta]:
        all_sets: List[Setlist] = []
        artist_name = None
        meta = SetlistMeta(total=0, items_per_page=0, pages_fetched=0, artist_name=None)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            # Fetch all pages in parallel
            tasks = [
                self._request(client, f"/artist/{mbid}/setlists", {"p": page})
                for page in range(1, max_pages + 1)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for page_idx, data in enumerate(results, start=1):
                # Skip if request failed or returned empty
                if isinstance(data, Exception) or not data:
                    break
                
                if page_idx == 1 and not artist_name:
                    page_sets = data.get("setlist", []) or []
                    if page_sets:
                        first_setlist = page_sets[0]
                        artist_info = first_setlist.get("artist", {})
                        if isinstance(artist_info, dict):
                            artist_name = artist_info.get("name")

                page_sets = data.get("setlist", []) or []
                for raw in page_sets:
                    songs = self._flatten_songs(raw)
                    setlist = Setlist(
                        id=raw.get("id", f"{mbid}:{page_idx}"),
                        event_date=_parse_event_date(raw.get("eventDate")),
                        tour=(raw.get("tour") or {}).get("name"),
                        songs=songs,
                    )
                    all_sets.append(setlist)

                meta = SetlistMeta(
                    total=int(data.get("total", meta.total or 0)),
                    items_per_page=int(data.get("itemsPerPage", meta.items_per_page or 0)),
                    pages_fetched=page_idx,
                    artist_name=artist_name,
                )

                if not page_sets:
                    break

        return all_sets, meta

    def _flatten_songs(self, payload: Dict) -> List[SongAppearance]:
        songs: List[SongAppearance] = []
        sets = (payload.get("sets") or {}).get("set", [])
        if isinstance(sets, dict):
            sets = [sets]
        for s in sets:
            tracks = s.get("song", [])
            if isinstance(tracks, dict):
                tracks = [tracks]
            for idx, track in enumerate(tracks, start=1):
                title = (track or {}).get("name")
                if title:
                    songs.append(SongAppearance(title=title.strip(), position=idx))
        return songs