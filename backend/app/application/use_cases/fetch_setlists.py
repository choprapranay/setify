from __future__ import annotations

from typing import Tuple

from ...domain.entities.models import Setlist, SetlistMeta
from ...domain.ports import SetlistRepository


class FetchSetlistsUseCase:
    def __init__(self, repository: SetlistRepository) -> None:
        self._repository = repository

    async def execute(self, mbid: str, *, pages: int) -> Tuple[list[Setlist], SetlistMeta]:
        return await self._repository.fetch_setlists(mbid, max_pages=pages)