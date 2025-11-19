import logging
from fastapi import APIRouter, Query, Depends, HTTPException

from backend.app.services.musicbrainz import search_artist_mb
from backend.app.services.setlistfm_client import SetlistFMClient
from backend.app.services.prediction import RecencyBetaPredictionService, PredictionConfigurationValues
from backend.app.services.spotify_client import SpotifyService

logger = logging.getLogger("setify.routes")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/api")

client = SetlistFMClient()
spotify_client = SpotifyService()
predictor = RecencyBetaPredictionService(
    PredictionConfigurationValues(half_life_days=180, alpha=1, beta=1, top_k=20,spotify_recency_boost=0,
        spotify_popularity_weight=0)
)

@router.get("/artist")
async def get_artist(artist: str = Query(...)):
    logger.info(f"/artist called with artist='{artist}'")

    try:
        result = search_artist_mb(artist)
    except Exception as exc:
        logger.exception(f"MusicBrainz lookup error: {exc}")
        raise HTTPException(500, "MusicBrainz error")

    if not result:
        logger.warning(f"Artist not found: {artist}")
        raise HTTPException(404, "Artist not found")

    logger.info(f"Artist resolved: {result}")
    return result

@router.get("/setlists")
async def get_setlists(
    mbid: str = Query(...),
    pages: int = Query(5)
):
    logger.info(f"/setlists called with mbid='{mbid}', pages={pages}")

    try:
        setlists, meta = await client.fetch_setlists(mbid, pages)
    except Exception as exc:
        logger.exception(f"Setlist.fm fetch error: {exc}")
        raise HTTPException(500, "Error fetching setlists")

    logger.info(f"Fetched {len(setlists)} setlists")
    return {"meta": meta, "setlists": setlists}

@router.get("/predict")
async def predict(
    mbid: str = Query(...),
    pages: int = Query(5),
    tour: str | None = Query(None),
):
    logger.info(f"/predict called with mbid={mbid}, pages={pages}, tour={tour}")

    # -----------------------------------------------------
    # FETCH SETLIST.FM DATA
    # -----------------------------------------------------
    try:
        setlists, meta = await client.fetch_setlists(mbid, pages)
    except Exception as exc:
        logger.exception(f"Error fetching setlists: {exc}")
        raise HTTPException(500, "Setlist fetch failed")

    if not setlists:
        logger.warning(f"No setlists found for MBID={mbid}")
        raise HTTPException(404, "No setlists found")

    # Extract artist name for Spotify lookup
    artist_name = getattr(meta, "artist_name", None)

    # -----------------------------------------------------
    #  FETCH NEW ALBUM TRACKS FROM SPOTIFY
    # -----------------------------------------------------
    new_album_tracks = []
    if artist_name:
        try:
            new_album_tracks = spotify_client.get_new_album_tracks(artist_name)
        except Exception as exc:
            logger.warning(f"Spotify lookup failed for artist '{artist_name}': {exc}")
            new_album_tracks = []

    try:
        combined_result = predictor.generate(
            setlists,
            artist_mbid=mbid,
            meta=meta,
            tour=tour,
            new_album_tracks=new_album_tracks
        )
    except Exception as exc:
        logger.exception(f"Prediction error: {exc}")
        raise HTTPException(500, "Prediction failed")


    logger.info(f"Prediction completed with {len(combined_result.songs)} songs")

    return {
        "artist_mbid": mbid,
        "artist_name": artist_name,
        "new_album_songs": new_album_tracks,
        "songs": combined_result.songs,
        "confidence": combined_result.confidence,
        "unique_songs": combined_result.unique_songs,
        "model_name": combined_result.model_name,
    }