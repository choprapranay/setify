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

