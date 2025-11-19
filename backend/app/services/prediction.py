# -----------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp, log
from statistics import median
from typing import Dict, Optional, List

from backend.app.entities.models import (PredictionSummary, Setlist, SetlistMeta, SongPrediction)

# -----------------------------------------------------------
# MAIN PREDICTION CLASS
# -----------------------------------------------------------
@dataclass
class PredictionConfigurationValues:
    half_life_days: int
    alpha: float
    beta: float
    top_k: int
    spotify_recency_boost: float
    spotify_popularity_weight: float

# -----------------------------------------------------------
# PREDICTION SERVICE
# -----------------------------------------------------------
class RecencyBetaPredictionService:
    def __init__(self, config: PredictionConfigurationValues) -> None:
        self.config = config

    def generate(self, setlists: list[Setlist], *, artist_mbid: str, meta: SetlistMeta, tour: Optional[str],
                 new_album_tracks: Optional[List[dict]] = None) -> PredictionSummary:

        config = self.config

        # FILTERING SETLISTS BY TOUR NAME
        filtered = [
            s for s in setlists
            if not tour or (s.tour or "").lower() == (tour or "").lower()
        ]
        if not filtered:
            raise ValueError("No setlists available for prediction")

        now = datetime.now(timezone.utc)

        # HALF-LIFE CALCULATION - FOR SONG WEIGHTING
        def weight_for(event_date: Optional[datetime]) -> float:
            if not event_date:
                return 1.0
            age_days = max(0, (now - event_date).days)
            return 0.5 ** (age_days / float(config.half_life_days))

        # Stats container for each song
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

            # DUPLICATE PREVENTION
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

                if setlist.event_date:
                    last_seen = stats["last_seen"]
                    if last_seen is None or setlist.event_date > last_seen:
                        stats["last_seen"] = setlist.event_date

        if used_shows == 0 or effective_shows == 0.0:
            raise ValueError("Insufficient song data for prediction")

        # SMOOTHED HISTORICAL PROBABILITY
        def smoothed_prob(weighted: float) -> float:
            return (weighted + config.alpha) / (effective_shows + config.alpha + config.beta)

        # Calculate base historical scores (recency-weighted)
        historical_scores = {
            title: smoothed_prob(stats["weighted"])
            for title, stats in song_stats.items()
        }

        # Calculate frequency-based scores (appearance rate, regardless of recency)
        # This ensures popular songs from older setlists aren't completely ignored
        frequency_scores = {
            title: stats["count"] / float(used_shows) if used_shows > 0 else 0.0
            for title, stats in song_stats.items()
        }

        # Hybrid scoring: combine recency-weighted (85%) with frequency-based (15%)
        # Favor newer songs more while still including historically popular songs
        hybrid_scores = {}
        for title in song_stats.keys():
            recency_score = historical_scores.get(title, 0.0)
            frequency_score = frequency_scores.get(title, 0.0)
            # Normalize frequency score to similar scale as recency score
            max_freq = max(frequency_scores.values()) if frequency_scores.values() else 1.0
            normalized_freq = frequency_score / max_freq if max_freq > 0 else 0.0
            # Weighted combination: 85% recency, 15% frequency (favors newer songs)
            hybrid_scores[title] = 0.85 * recency_score + 0.15 * normalized_freq

        total_hybrid = sum(hybrid_scores.values()) or 1.0
        hybrid_scores = {k: v / total_hybrid for k, v in hybrid_scores.items()}

        if new_album_tracks:
            final_scores = {song: float(score) for song, score in hybrid_scores.items()}

            for track in new_album_tracks:
                title = track["name"]
                popularity = track.get("popularity", 50)

                pop_norm = popularity / 100.0

                if title not in final_scores:
                    final_scores[title] = 0.0

                final_scores[title] += config.spotify_recency_boost
                final_scores[title] += config.spotify_popularity_weight * pop_norm

            total = sum(final_scores.values()) or 1.0
            final_scores = {k: v / total for k, v in final_scores.items()}

        else:
            final_scores = hybrid_scores

        # Sort by score and take top_k
        ranked_final = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[: config.top_k]
        
        # Apply power scaling to concentrate probability on top songs
        # This makes the top songs have much higher probabilities (e.g., top song ~60-70%)
        # Using power of 2.5 to create a strong concentration effect
        POWER_SCALE = 2.5
        scaled_scores = [(title, prob ** POWER_SCALE) for title, prob in ranked_final]
        
        # RE-NORMALIZE after scaling so probabilities sum to 1.0
        scaled_total = sum(prob for _, prob in scaled_scores) or 1.0
        ranked_final = [(title, prob / scaled_total) for title, prob in scaled_scores]

        songs = []
        for title, prob in ranked_final:
            stats = song_stats.get(title, None)

            songs.append(
                SongPrediction(
                    title=title,
                    probability=round(prob, 4),
                    appearances=stats["count"] if stats else 0,
                    weighted_appearances=round(stats["weighted"], 3) if stats else 0.0,
                    typical_position=int(median(stats["positions"])) if stats and stats["positions"] else None,
                    last_seen=stats["last_seen"] if stats else None,
                )
            )

        all_probs = list(historical_scores.values())
        prob_total = sum(all_probs)
        normalized = [p / prob_total for p in all_probs] if prob_total > 0 else []

        entropy = -sum(p * log(p) for p in normalized if p > 0)
        max_entropy = log(max(1, len(normalized))) if normalized else 0.0
        sharpness = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        sample_factor = 1.0 - exp(-effective_shows / 5.0)
        confidence = min(0.98, max(0.0, round(0.5 * sharpness + 0.5 * sample_factor, 3)))

        return PredictionSummary(
            artist_mbid=artist_mbid,
            tour=tour,
            sets_considered=used_shows,
            effective_shows=round(effective_shows, 3),
            unique_songs=len(song_stats),
            confidence=confidence,
            songs=songs,
            model_name="recency_beta_v3+power_scaled",
            model_params={
                "half_life_days": config.half_life_days,
                "alpha": config.alpha,
                "beta": config.beta,
                "top_k": config.top_k,
                "spotify_recency_boost": config.spotify_recency_boost,
                "spotify_popularity_weight": config.spotify_popularity_weight,
            },
            meta=meta,
        )
