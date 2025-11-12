from __future__ import annotations
from typing import Optional, Protocol, Tuple

from .entities.models import Artist, Setlist, SetlistMeta

class ArtistRepository(Protocol):
    async def search_artist(self, name: str) -> Optional[Artist]:
        ...

class SetlistRepository(Protocol):
    async def fetch_setlists(self, mbid:str, max_pages:int) -> Tuple[list[Setlist], SetlistMeta]:
        ...
