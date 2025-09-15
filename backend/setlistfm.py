# setify/backend/setlistfm.py
import os
from typing import Dict, List, Optional, Tuple
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("SETLISTFM_BASE", "https://api.setlist.fm/rest/1.0")
API_KEY = os.getenv("SETLISTFM_API_KEY", "")
LANG = os.getenv("SETLISTFM_LANG", "en")  # optional UI language

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",      # required for JSON
    "Accept-Language": LANG,           # optional
}

HTTP_TIMEOUT = httpx.Timeout(30.0)

class SetlistError(Exception):
    pass

async def _request(client: httpx.AsyncClient, path: str, params: Dict) -> Dict:
    r = await client.get(f"{BASE}{path}", params=params, headers=HEADERS)
    if r.status_code == 404:
        return {}  # treat as empty
    if r.status_code == 429:
        # respect Retry-After if provided
        retry = int(r.headers.get("Retry-After", "1"))
        await asyncio.sleep(min(retry, 5))
        r = await client.get(f"{BASE}{path}", params=params, headers=HEADERS)
    r.raise_for_status()
    return r.json()

async def search_artist(name: str) -> Optional[Dict]:
    """Return the best-matching artist dict (or None)."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        data = await _request(client, "/search/artists", {"artistName": name, "p": 1})
        artists = data.get("artist", []) if data else []
        if not artists:
            return None
        exact = next((a for a in artists if a.get("name", "").lower() == name.lower()), None)
        return exact or artists[0]

async def fetch_setlists(
    mbid: str,
    max_pages: int = 5,
    per_page_hint: int = 20
) -> Tuple[List[Dict], Dict]:
    """
    Fetch up to max_pages of setlists for an artist MBID.
    Returns (setlists, meta) where meta includes total/itemsPerPage/pagesFetched.
    """
    all_sets: List[Dict] = []
    meta = {"total": 0, "itemsPerPage": 0, "pagesFetched": 0}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        for p in range(1, max_pages + 1):
            data = await _request(
                client,
                f"/artist/{mbid}/setlists",
                {"p": p}
            )
            if not data:
                break
            page_sets = data.get("setlist", []) or []
            all_sets.extend(page_sets)

            # capture meta from the envelope (if present)
            meta["total"] = int(data.get("total", meta["total"] or 0))
            meta["itemsPerPage"] = int(data.get("itemsPerPage", meta["itemsPerPage"] or 0))
            meta["pagesFetched"] = p

            if not page_sets:
                break

    return all_sets, meta

def flatten_songs(one_setlist: Dict) -> List[str]:
    """
    Extract song titles from a setlist payload.
    Structure: setlist -> sets -> set (list) -> song (list of dicts with 'name').
    """
    out: List[str] = []
    sets = (one_setlist.get("sets") or {}).get("set", [])
    if isinstance(sets, dict):
        sets = [sets]
    for s in sets:
        songs = s.get("song", [])
        if isinstance(songs, dict):
            songs = [songs]
        for g in songs:
            name = (g or {}).get("name")
            if name:
                out.append(name.strip())
    return out
