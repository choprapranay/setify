import logging
from fastapi import APIRouter, Query, Depends, HTTPException

from backend.app.services.musicbrainz import search_artist_mb
from backend.app.services.setlistfm_client import SetlistFMClient
from backend.app.services.prediction import RecencyBetaPredictionService, PredictionConfig

logger = logging.getLogger("setify.routes")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/api")

client = SetlistFMClient()
predictor = RecencyBetaPredictionService(
    PredictionConfig(half_life_days=180, alpha=1.0, beta=1.0, top_k=20)
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

    try:
        setlists, meta = await client.fetch_setlists(mbid, pages)
    except Exception as exc:
        logger.exception(f"Error fetching setlists: {exc}")
        raise HTTPException(500, "Setlist fetch failed")

    if not setlists:
        logger.warning(f"No setlists found for MBID={mbid}")
        raise HTTPException(404, "No setlists found")

    try:
        result = predictor.generate(
            setlists,
            artist_mbid=mbid,
            meta=meta,
            tour=tour
        )
    except Exception as exc:
        logger.exception(f"Prediction error: {exc}")
        raise HTTPException(500, "Prediction failed")

    logger.info(f"Prediction completed: {len(result.songs)} songs")
    return result
