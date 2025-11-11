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
