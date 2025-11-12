from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp, log
from statistics import median
from typing import Dict, Optional

from ..entities.models import PredictionSummary, Setlist, SetlistMeta, SongPrediction


@dataclass
class PredictionConfig:
    half_life_days: int
    alpha: float
    beta: float
    top_k: int


class RecencyBetaPredictionService:
    """Implements the weighted prediction algorithm using clean architecture primitives."""

    def __init__(self, config: PredictionConfig) -> None:
        self.config = config

    def generate(
        self,
        setlists: list[Setlist],
        *,
        artist_mbid: str,
        meta: SetlistMeta,
        tour: Optional[str],
        half_life_days: Optional[int] = None,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> PredictionSummary:
        cfg = PredictionConfig(
            half_life_days=half_life_days or self.config.half_life_days,
            alpha=alpha if alpha is not None else self.config.alpha,
            beta=beta if beta is not None else self.config.beta,
            top_k=top_k or self.config.top_k,
        )

        filtered = [s for s in setlists if not tour or (s.tour or "").lower() == (tour or "").lower()]
        if not filtered:
            raise ValueError("No setlists available for prediction")

        now = datetime.now(timezone.utc)

        def weight_for(event_date: Optional[datetime]) -> float:
            if not event_date:
                return 1.0
            age_days = max(0, (now - event_date).days)
            return 0.5 ** (age_days / float(cfg.half_life_days))

        song_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                "count": 0,
                "weighted": 0.0,
                "positions": [],
                "last_seen": None,
            }
        )

        effective_shows = 0.0
        used_shows = 0

        for setlist in filtered:
            if not setlist.songs:
                continue

            seen = set()
            unique_order = []
            for song in setlist.songs:
                if song.title not in seen:
                    seen.add(song.title)
                    unique_order.append(song)

            weight = weight_for(setlist.event_date)
            effective_shows += weight
            used_shows += 1

            for song in unique_order:
                stats = song_stats[song.title]
                stats["count"] += 1
                stats["weighted"] += weight
                stats["positions"].append(song.position)
                if setlist.event_date is not None:
                    last_seen = stats["last_seen"]
                    if last_seen is None or setlist.event_date > last_seen:
                        stats["last_seen"] = setlist.event_date

        if used_shows == 0 or effective_shows == 0.0:
            raise ValueError("Insufficient song data for prediction")

        def smoothed_prob(weighted: float) -> float:
            return (weighted + cfg.alpha) / (effective_shows + cfg.alpha + cfg.beta)

        all_probs = [smoothed_prob(stats["weighted"]) for stats in song_stats.values()]
        entropy = -sum(p * log(p) for p in all_probs if p > 0)
        max_entropy = log(max(1, len(all_probs)))
        sharpness = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        sample_factor = 1.0 - exp(-effective_shows / 5.0)
        confidence = min(0.98, round(0.5 * sharpness + 0.5 * sample_factor, 3))

        ranked = sorted(
            song_stats.items(),
            key=lambda item: smoothed_prob(item[1]["weighted"]),
            reverse=True,
        )[: cfg.top_k]

        songs = [
            SongPrediction(
                title=title,
                probability=round(smoothed_prob(stats["weighted"]), 4),
                appearances=stats["count"],
                weighted_appearances=round(stats["weighted"], 3),
                typical_position=int(median(stats["positions"])) if stats["positions"] else None,
                last_seen=stats["last_seen"],
            )
            for title, stats in ranked
        ]

        return PredictionSummary(
            artist_mbid=artist_mbid,
            tour=tour,
            sets_considered=used_shows,
            effective_shows=round(effective_shows, 3),
            unique_songs=len(song_stats),
            confidence=confidence,
            songs=songs,
            model_name="recency_beta_v1",
            model_params={
                "half_life_days": cfg.half_life_days,
                "alpha": cfg.alpha,
                "beta": cfg.beta,
                "top_k": cfg.top_k,
            },
            meta=meta,
        )