from __future__ import annotations
from typing import Optional, Protocol, Tuple

from .entities.models import Artist, PredictionSummary, Setlist, SetlistMeta

class ArtistRepository(Protocol):
    async def search_artist(self, name: str) -> Optional[Artist]:
        ...

class SetlistRepository(Protocol):
    async def fetch_setlists(self, mbid:str, max_pages:int) -> Tuple[list[Setlist], SetlistMeta]:
        ...

class PredictionService(Protocol):
    def generate(
        self,
        setlists: list[Setlist],
        *,
        artist_mbid: str,
        meta: SetlistMeta,
        tour: Optional[str],
        half_life_days: int,
        alpha: float,
        beta: float,
        top_k: int,
    ) -> PredictionSummary:
        ...