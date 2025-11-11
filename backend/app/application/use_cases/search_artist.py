from __future__ import annotations

from typing import Optional

from ...domain.entities.models import Artist
from ...domain.ports import ArtistRepository


class SearchArtistUseCase:
    def __init__(self, repository: ArtistRepository) -> None:
        self._repository = repository

    async def execute(self, name: str) -> Optional[Artist]:
        return await self._repository.search_artist(name)