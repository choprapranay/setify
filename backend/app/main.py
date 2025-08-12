from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .setlistfm import search_artist, fetch_setlists

API = FastAPI(title="Setify API")

# Frontend Connection
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


@API.get("/api/predict")
def predict(artist: str, tour: str = None):
    return {
        "artist": artist,
        "tour": tour,
        "total_setlists": 24,
        "confidence": 0.78,
        "songs": [
            {"title": "Sample Song A", "probability": 0.16, "appearances": 20},
            {"title": "Sample Song B", "probability": 0.12, "appearances": 18},
            {"title": "Sample Song C", "probability": 0.10, "appearances": 17},
            {"title": "Sample Song D", "probability": 0.08, "appearances": 15},
        ],
    }

