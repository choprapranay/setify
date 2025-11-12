from __future__ import annotations

from typing import Optional

from ...domain.entities.models import PredictionSummary, Setlist, SetlistMeta
from ...domain.ports import PredictionService


class PredictSetlistUseCase:
    def __init__(self, service: PredictionService) -> None:
        self._service = service

    def execute(
        self,
        setlists: list[Setlist],
        *,
        artist_mbid: str,
        meta: SetlistMeta,
        tour: Optional[str],
        top_k: int,
        half_life_days: int,
        alpha: float,
        beta: float,
    ) -> PredictionSummary:
        return self._service.generate(
            setlists,
            artist_mbid=artist_mbid,
            meta=meta,
            tour=tour,
            half_life_days=half_life_days,
            alpha=alpha,
            beta=beta,
            top_k=top_k,
        )