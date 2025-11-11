import os
from typing import Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("SETLISTFM_BASE", "https://api.setlist.fm/rest/1.0")
HEADERS = {
    "x-api-key": os.getenv("SETLISTFM_API_KEY", ""),
    "Accept": "application/json",
}

async def search_artist(name: str) -> Optional[Dict]:
    url = f"{BASE}/search/artists"
    params = {"artistName": name, "p": 1}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params, headers=HEADERS)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        artists = data.get("artist", [])
        if not artists:
            return None

        exact = next((a for a in artists if a.get("name", "").lower() == name.lower()), None)
        return exact or artists[0]

async def fetch_setlists(artist_mbid: str, tour: Optional[str], max_pages: int = 3) -> List[Dict]:
    all_sets: List[Dict] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, max_pages + 1):
            params = {"artistMbid": artist_mbid, "p": page}
            if tour:
                params["tourName"] = tour
            r = await client.get(f"{BASE}/search/setlists", params=params, headers=HEADERS)
            if r.status_code == 404:
                break
            r.raise_for_status()
            page_sets = r.json().get("setlist", [])
            if not page_sets:
                break
            all_sets.extend(page_sets)
    return all_sets