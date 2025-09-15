from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import median
from math import log, exp
from typing import Optional, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.setlistfm import search_artist, fetch_setlists, flatten_songs

API = FastAPI(title="Setify API")

API.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Function
def _parse_event_date(sl) -> Optional[datetime]:
    raw = sl.get("eventDate")
    if not raw:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            # make it timezone-aware (treat as midnight local; store as UTC)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None

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


@API.get("/api/predict")
async def predict(
    mbid: str = Query(..., min_length=10),
    pages: int = Query(5, ge=1, le=10),
    tour: Optional[str] = None,
    top_k: int = Query(20, ge=1, le=50),

    half_life_days: int = Query(180, ge=7, le=1000, description="Recency half-life in days"),
    alpha: float = Query(1.0, ge=0.0, le=5.0, description="Beta prior α"),
    beta: float  = Query(1.0, ge=0.0, le=5.0, description="Beta prior β"),
):

    sets, meta = await fetch_setlists(mbid, max_pages=pages)
    if tour:
        sets = [s for s in sets if (s.get("tour") or {}).get("name", "").lower() == tour.lower()]
    if not sets:
        raise HTTPException(status_code=404, detail="No setlists found for prediction")

    now = datetime.now(timezone.utc)
    def weight_for(sl) -> float:
        dt = _parse_event_date(sl)
        if not dt:
            return 1.0
        age_days = max(0, (now - dt).days)
        return 0.5 ** (age_days / float(half_life_days))

    effective_shows = 0.0
    song_stats: Dict[str, Dict] = defaultdict(lambda: {
        "count": 0,
        "weighted": 0.0,
        "positions": [],
        "last_seen": None,
    })

    used_shows = 0

    for sl in sets:
        titles: List[str] = flatten_songs(sl)
        if not titles:
            continue

        seen = set()
        unique_in_order = []
        for idx, t in enumerate(titles, start=1):
            if t not in seen:
                unique_in_order.append((t, idx))
                seen.add(t)

        w = weight_for(sl)
        effective_shows += w
        used_shows += 1

        dt = _parse_event_date(sl)

        for title, pos in unique_in_order:
            st = song_stats[title]
            st["count"] += 1
            st["weighted"] += w
            st["positions"].append(pos)
            if dt is not None:
                if st["last_seen"] is None or dt > st["last_seen"]:
                    st["last_seen"] = dt

    if used_shows == 0 or effective_shows == 0.0:
        raise HTTPException(status_code=404, detail="No songs found in setlists")

    def smoothed_prob(weighted: float) -> float:
        return (weighted + alpha) / (effective_shows + alpha + beta)

    all_probs: List[float] = []
    for st in song_stats.values():
        all_probs.append(smoothed_prob(st["weighted"]))

    N = max(1, len(all_probs))
    entropy = -sum(p * log(p) for p in all_probs if p > 0)
    max_entropy = log(N)
    sharpness = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
    sample_factor = 1.0 - exp(-effective_shows / 5.0)
    confidence = min(0.98, round(0.5 * sharpness + 0.5 * sample_factor, 3))

    ranked = sorted(
        song_stats.items(),
        key=lambda kv: smoothed_prob(kv[1]["weighted"]),
        reverse=True,
    )[:top_k]

    def fmt_date(dt: Optional[datetime]) -> Optional[str]:
        return dt.date().isoformat() if dt else None

    songs = [
        {
            "title": title,
            "probability": round(smoothed_prob(st["weighted"]), 4),
            "appearances": st["count"],
            "weighted_appearances": round(st["weighted"], 3),
            "typical_position": int(median(st["positions"])) if st["positions"] else None,
            "last_seen": fmt_date(st["last_seen"]),
        }
        for title, st in ranked
    ]

    return {
        "model": {
            "name": "recency_beta_v1",
            "half_life_days": half_life_days,
            "alpha": alpha,
            "beta": beta,
        },
        "artist_mbid": mbid,
        "tour": tour,
        "sets_considered": used_shows,
        "effective_shows": round(effective_shows, 3),
        "unique_songs": len(song_stats),
        "meta": meta,
        "confidence": confidence,
        "songs": songs,
    }