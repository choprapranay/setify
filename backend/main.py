from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from collections import Counter
from math import sqrt
from typing import Optional, Dict

from backend.setlistfm import search_artist, fetch_setlists, flatten_songs

API = FastAPI(title="Setify API")

API.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@API.get("/api/artist")
async def get_artist(artist: str = Query(..., min_length=2)):
    a = await search_artist(artist)
    if not a:
        raise HTTPException(status_code=404, detail="Artist not found")
    return {"name": a.get("name"), "mbid": a.get("mbid")}

@API.get("/api/setlists")
async def get_setlists(
    mbid: str = Query(..., min_length=10),
    pages: int = Query(3, ge=1, le=10),
    tour: Optional[str] = None
):
    sets, meta = await fetch_setlists(mbid, max_pages=pages)
    if tour:
        sets = [s for s in sets if (s.get("tour") or {}).get("name", "").lower() == tour.lower()]
    return {"meta": meta, "count": len(sets), "setlists": sets}

#TO-DO: Need to make beter
@API.get("/api/predict")
async def predict(
    mbid: str = Query(..., min_length=10),
    pages: int = Query(5, ge=1, le=10),
    tour: Optional[str] = None,
    top_k: int = Query(20, ge=1, le=50)
):

    sets, meta = await fetch_setlists(mbid, max_pages=pages)
    if tour:
        sets = [s for s in sets if (s.get("tour") or {}).get("name", "").lower() == tour.lower()]

    if not sets:
        raise HTTPException(status_code=404, detail="No setlists found for prediction")

    song_counts = Counter()
    appearances_by_song: Dict[str, int] = {}
    num_sets_used = 0

    for sl in sets:
        titles = flatten_songs(sl)
        if titles:
            num_sets_used += 1
            for t in set(titles):
                song_counts[t] += 1

    if num_sets_used == 0:
        raise HTTPException(status_code=404, detail="No songs found in setlists")

    ranked = song_counts.most_common(top_k)
    songs = [
        {
            "title": title,
            "probability": round(count / num_sets_used, 4),
            "appearances": count,
        }
        for title, count in ranked
    ]

    confidence = min(0.98, round(sqrt(num_sets_used) / 5, 3))

    return {
        "artist_mbid": mbid,
        "tour": tour,
        "sets_considered": num_sets_used,
        "meta": meta,
        "confidence": confidence,
        "songs": songs,
    }
