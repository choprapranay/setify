from fastapi import APIRouter, Query, Depends, HTTPException

from backend.app.services.musicbrainz import search_artist_mb
from backend.app.services.setlistfm_client import SetlistFMClient
from backend.app.services.prediction import RecencyBetaPredictionService, PredictionConfigurationValues
from backend.app.services.spotify_client import SpotifyService

router = APIRouter(prefix="/api")

client = SetlistFMClient()
spotify_client = SpotifyService()

# Prediction Model
predictor = RecencyBetaPredictionService(
    PredictionConfigurationValues(
        half_life_days=240,  
        top_k=28,  
        spotify_recency_boost=0.20,  
        spotify_popularity_weight=0.30,  
        spotify_top_track_boost=0.20  
    )
)

@router.get("/artist")
async def get_artist(artist: str = Query(...)):
    try:
        result = search_artist_mb(artist)
    except Exception as exc:
        raise HTTPException(500, "MusicBrainz error")

    if not result:
        raise HTTPException(404, "Artist not found")

    return result

@router.get("/setlists")
async def get_setlists(mbid: str = Query(...), pages: int = Query(5)):
    try:
        setlists, meta = await client.fetch_setlists(mbid, pages)
    except Exception as exc:
        raise HTTPException(500, "Error fetching setlists")

    return {"meta": meta, "setlists": setlists}

@router.get("/predict")
async def predict(mbid: str = Query(...), pages: int = Query(5)):

    # -----------------------------------------------------
    # FETCH SETLIST.FM DATA
    # -----------------------------------------------------
    try:
        setlists, meta = await client.fetch_setlists(mbid, pages)
    except Exception as exc:
        raise HTTPException(500, "Setlist fetch failed")

    if not setlists:
        raise HTTPException(404, "No setlists found")

    artist_name = meta.artist_name

    # -----------------------------------------------------
    # FETCH SPOTIFY TRACK DATA
    # -----------------------------------------------------
    spotify_track_matches = {}
    all_spotify_tracks = {}
    if artist_name:
        try:
            all_setlist_songs = set()
            for setlist in setlists:
                for song in setlist.songs:
                    all_setlist_songs.add(song.title)
            
            all_spotify_tracks = spotify_client.get_artist_track_data(artist_name)
            
            spotify_track_matches = spotify_client.match_setlist_songs_to_spotify(
                list(all_setlist_songs), 
                artist_name
            )
        except ValueError as exc:
            spotify_track_matches = {}
            all_spotify_tracks = {}
        except Exception as exc:
            spotify_track_matches = {}
            all_spotify_tracks = {}

    # -----------------------------------------------------
    # PREDICTION PROCESS
    # -----------------------------------------------------
    try:
        combined_result = predictor.generate(
            setlists,
            artist_mbid=mbid,
            meta=meta,
            spotify_track_matches=spotify_track_matches,
            all_spotify_tracks=all_spotify_tracks,
            artist_name=artist_name
        )
    except Exception as exc:
        raise HTTPException(500, "Prediction failed")

    return {
        "artist_mbid": mbid,
        "artist_name": artist_name,
        "spotify_matches": len(spotify_track_matches),
        "songs": [
            {
                "title": song.title,
                "probability": song.probability,
                "appearances": song.appearances,
                "weighted_appearances": song.weighted_appearances,
                "typical_position": song.typical_position,
                "last_seen": song.last_seen.isoformat() if song.last_seen else None,
                "spotify_track_id": song.spotify_track_id,
            }
            for song in combined_result.songs
        ],
        "model_name": combined_result.model_name,
        "meta": {
            "pages_fetched": meta.pages_fetched if meta else 0,
        }
    }