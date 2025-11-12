from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.use_cases.fetch_setlists import FetchSetlistsUseCase
from ...application.use_cases.search_artist import SearchArtistUseCase
from ...infrastructure.setlistfm_client import SetlistFMClient

router = APIRouter(prefix="/api")

_client = SetlistFMClient()

async def get_client() -> SetlistFMClient:
    return _client

@router.get("/artist")
async def get_artist(
    artist: str = Query(..., min_length=2),
    client: SetlistFMClient = Depends(get_client),
):
    use_case = SearchArtistUseCase(client)
    found = await use_case.execute(artist)
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

