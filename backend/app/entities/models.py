from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Artist:
    name: str
    mbid: str

@dataclass
class SongAppearance:
    title: str
    position: int

@dataclass
class SetlistMeta:
    total: int
    items_per_page: int
    pages_fetched: int

@dataclass
class Setlist:
    id: str
    event_date: Optional[datetime]
    tour: Optional[str]
    songs: List[SongAppearance]

@dataclass
class SongPrediction:
    title: str
    probability: float
    appearances: int
    weighted_appearances: float
    typical_position: Optional[int]
    last_seen: Optional[datetime]


@dataclass
class PredictionSummary:
    artist_mbid: str
    tour: Optional[str]
    sets_considered: int
    effective_shows: float
    unique_songs: int
    confidence: float
    songs: List[SongPrediction]
    model_name: str
    model_params: dict
    meta: SetlistMeta