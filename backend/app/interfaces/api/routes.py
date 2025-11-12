from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.use_cases.fetch_setlists import FetchSetlistsUseCase
from ...application.use_cases.predict_setlist import PredictSetlistUseCase
from ...application.use_cases.search_artist import SearchArtistUseCase
from ...domain.services.prediction import PredictionConfig, RecencyBetaPredictionService
from ...infrastructure.setlistfm_client import SetlistFMClient, SetlistFMCredentialsError

router = APIRouter(prefix="/api")

_client = SetlistFMClient()
_service = RecencyBetaPredictionService(
    PredictionConfig(half_life_days=180, alpha=1.0, beta=1.0, top_k=20)
)


async def get_client() -> SetlistFMClient:
    return _client


def get_prediction_service() -> RecencyBetaPredictionService:
    return _service


@router.get("/artist")
async def get_artist(
    artist: str = Query(..., min_length=2),
    client: SetlistFMClient = Depends(get_client),
):
    use_case = SearchArtistUseCase(client)
    try:
        found = await use_case.execute(artist)
    except SetlistFMCredentialsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not found:
        raise HTTPException(status_code=404, detail="Artist not found")
    return {"name": found.name, "mbid": found.mbid}


@router.get("/setlists")
async def get_setlists(
    mbid: str = Query(..., min_length=10),
    pages: int = Query(3, ge=1, le=10),
    client: SetlistFMClient = Depends(get_client),
):
    use_case = FetchSetlistsUseCase(client)
    setlists, meta = await use_case.execute(mbid, pages=pages)
    payload = []
    for sl in setlists:
        payload.append(
            {
                "id": sl.id,
                "event_date": sl.event_date.date().isoformat() if sl.event_date else None,
                "tour": sl.tour,
                "songs": [
                    {"title": song.title, "position": song.position}
                    for song in sl.songs
                ],
            }
        )
    return {
        "meta": {
            "total": meta.total,
            "items_per_page": meta.items_per_page,
            "pages_fetched": meta.pages_fetched,
        },
        "count": len(setlists),
        "setlists": payload,
    }


@router.get("/predict")
async def predict(
    mbid: str = Query(..., min_length=10),
    pages: int = Query(5, ge=1, le=10),
    tour: str | None = Query(None),
    top_k: int = Query(20, ge=1, le=50),
    half_life_days: int = Query(180, ge=7, le=1000),
    alpha: float = Query(1.0, ge=0.0, le=5.0),
    beta: float = Query(1.0, ge=0.0, le=5.0),
    client: SetlistFMClient = Depends(get_client),
    service: RecencyBetaPredictionService = Depends(get_prediction_service),
):
    fetch_use_case = FetchSetlistsUseCase(client)
    setlists, meta = await fetch_use_case.execute(mbid, pages=pages)
    if not setlists:
        raise HTTPException(status_code=404, detail="No setlists found for prediction")

    predict_use_case = PredictSetlistUseCase(service)
    try:
        result = predict_use_case.execute(
            setlists,
            artist_mbid=mbid,
            meta=meta,
            tour=tour,
            top_k=top_k,
            half_life_days=half_life_days,
            alpha=alpha,
            beta=beta,
        )
    except ValueError as exc:  # domain validation
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "model": {"name": result.model_name, **result.model_params},
        "artist_mbid": result.artist_mbid,
        "tour": result.tour,
        "sets_considered": result.sets_considered,
        "effective_shows": result.effective_shows,
        "unique_songs": result.unique_songs,
        "meta": {
            "total": result.meta.total,
            "items_per_page": result.meta.items_per_page,
            "pages_fetched": result.meta.pages_fetched,
        },
        "confidence": result.confidence,
        "songs": [
            {
                "title": song.title,
                "probability": song.probability,
                "appearances": song.appearances,
                "weighted_appearances": song.weighted_appearances,
                "typical_position": song.typical_position,
                "last_seen": song.last_seen.date().isoformat() if song.last_seen else None,
            }
            for song in result.songs
        ],
    }