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
# HELPER FUNCTIONS
# -----------------------------------------------------------
def _normalize_song_name(name: str) -> str:
    """Normalize song name for matching"""
    name = name.lower().strip()
    name = name.replace("(live)", "").replace("[live]", "").replace("(remix)", "").replace("[remix]", "")
    name = name.replace("(feat.", "(ft.").replace("(ft.", "").replace("featuring", "ft")
    name = " ".join(name.split())
    return name

# -----------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------
@dataclass
class PredictionConfigurationValues:
    half_life_days: int
    top_k: int
    spotify_recency_boost: float
    spotify_popularity_weight: float
    spotify_top_track_boost: float

# -----------------------------------------------------------
# PREDICTION SERVICE
# -----------------------------------------------------------
class RecencyBetaPredictionService:
    def __init__(self, config: PredictionConfigurationValues) -> None:
        self.config = config

    def generate(self, setlists: list[Setlist], *, artist_mbid: str, meta: SetlistMeta, spotify_track_matches: Optional[Dict[str, Dict]] = None,
        all_spotify_tracks: Optional[Dict[str, Dict]] = None, artist_name: Optional[str] = None) -> PredictionSummary:

        config = self.config
        now = datetime.now(timezone.utc)

        # ============================================================
        # COLLECT SETLIST.FM DATA
        # ============================================================
        song_data = defaultdict(lambda: {
            "count": 0,
            "weighted_count": 0.0,
            "positions": [],
            "last_seen": None,
        })
        
        total_weight = 0.0
        total_shows = 0
        
        setlist_songs = {}  
        
        for setlist in setlists:
            if not setlist.songs:
                continue
            
        # ============================================================
        # CALCULATE RECENCY WEIGHT FOR SETLIST
        # ============================================================
            age_days = (now - setlist.event_date).days if setlist.event_date else 0
            recency_weight = 0.5 ** (age_days / config.half_life_days)
            total_weight += recency_weight
            total_shows += 1
            
            seen_in_setlist = set()
            for song in setlist.songs:
                if song.title in seen_in_setlist:
                    continue
                seen_in_setlist.add(song.title)
                
                normalized = _normalize_song_name(song.title)
                setlist_songs[normalized] = song.title
                
                data = song_data[song.title]
                data["count"] += 1
                data["weighted_count"] += recency_weight
                data["positions"].append(song.position)
                
                if setlist.event_date:
                    if data["last_seen"] is None or setlist.event_date > data["last_seen"]:
                        data["last_seen"] = setlist.event_date

        if total_shows == 0:
            raise ValueError("No setlist data available")

        # ============================================================
        # MATCH CURRENT SONGS IN SETLIST WITH SPOTIFY DATA
        # ============================================================
        spotify_data = spotify_track_matches or {}
        all_spotify = all_spotify_tracks or {}
        
        name_mapping = {} 
        
        for setlist_name in song_data.keys():
            if setlist_name in spotify_data:
                spotify_info = spotify_data[setlist_name]
                spotify_name = spotify_info.get("name", setlist_name)
                name_mapping[setlist_name] = spotify_name
        
        # ============================================================
        # CALCULATE SCORES FOR SETLIST.FM SONGS
        # ============================================================
        scores = {}
        
        max_weighted = max(d["weighted_count"] for d in song_data.values()) if song_data else 1.0
        max_count = max(d["count"] for d in song_data.values()) if song_data else 1.0
        
        for song_name, data in song_data.items():
            weighted_score = (data["weighted_count"] / max_weighted) if max_weighted > 0 else 0.0
            frequency_score = (data["count"] / max_count) if max_count > 0 else 0.0
            
            base_score = 0.7 * weighted_score + 0.3 * frequency_score
            
            # APPLY SPOTIFY BOOST IF AVAILABLE
            if song_name in spotify_data:
                spotify_info = spotify_data[song_name]
                boost = 0.0
                
                if spotify_info.get("source") == "top_tracks":
                    boost += config.spotify_top_track_boost
                if spotify_info.get("source") == "new_album":
                    boost += config.spotify_recency_boost
                
                popularity = spotify_info.get("popularity", 0)
                if popularity > 0:
                    boost += config.spotify_popularity_weight * (popularity / 100.0)
                
                base_score *= (1.0 + boost * 0.3)  
            
            scores[song_name] = base_score

        # ============================================================
        # ADD NEW SPOTIFY SONGS (not in current setlist)
        # ============================================================
        new_album_tracks_found = []
        if all_spotify:
            for normalized_name, spotify_info in all_spotify.items():
                spotify_name = spotify_info.get("name", "")
                popularity = spotify_info.get("popularity", 0)
                source = spotify_info.get("source", "")
                
                is_duplicate = False
                
                if normalized_name in setlist_songs:
                    is_duplicate = True
                else:
                    for setlist_norm, setlist_orig in setlist_songs.items():
                        shorter = normalized_name if len(normalized_name) < len(setlist_norm) else setlist_norm
                        longer = normalized_name if len(normalized_name) >= len(setlist_norm) else setlist_norm
                        
                        if len(shorter) >= 5 and shorter in longer and len(shorter) >= len(longer) * 0.7:
                            is_duplicate = True
                            name_mapping[setlist_orig] = spotify_name
                            break
                
                if is_duplicate or spotify_name in scores:
                    continue
                
                should_add = False
                if source == "top_tracks" and popularity >= 40:
                    should_add = True
                elif source == "new_album" and popularity >= 25:  
                    should_add = True
                
                if should_add:
                    setlist_scores_list = sorted(scores.values()) if scores else []
                    if setlist_scores_list:
                        median_setlist_score = setlist_scores_list[len(setlist_scores_list) // 2]
                        min_setlist_score = setlist_scores_list[0]  
                    else:
                        median_setlist_score = 0.5 
                        min_setlist_score = 0.2
                    
                    sorted_scores = sorted(setlist_scores_list, reverse=True)  
                    if len(sorted_scores) >= config.top_k:
                        baseline_score = sorted_scores[config.top_k - 1]
                    elif sorted_scores:
                        baseline_score = sorted_scores[-1]
                    else:
                        baseline_score = 0.3  
                    
                    if source == "top_tracks":
                        popularity_scale = 1.0 + (popularity / 100.0) * 0.5
                        new_score = baseline_score * 0.90 * popularity_scale
                    else:  
                        popularity_scale = 1.0 + (popularity / 100.0) * 0.8  
                        new_score = baseline_score * 0.95 * popularity_scale
                    
                    min_threshold = max(baseline_score * 0.90, 0.25)  
                    new_score = max(new_score, min_threshold)
                    
                    scores[spotify_name] = new_score
                    
                    if source == "new_album":
                        new_album_tracks_found.append((spotify_name, popularity, new_score))

        
        # ============================================================
        # UPDATE NAMES AND RANK
        # ============================================================
        final_scores = {}
        for song_name, score in scores.items():
            display_name = name_mapping.get(song_name, song_name)
            if display_name in final_scores:
                final_scores[display_name] = max(final_scores[display_name], score)
            else:
                final_scores[display_name] = score

        ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:config.top_k]
        
        # ============================================================
        # NORMALIZE TO PROBABILITIES
        # ============================================================
        total_score = sum(score for _, score in ranked) or 1.0
        
        predictions = []
        
        display_to_original = {v: k for k, v in name_mapping.items()}
        
        for song_name, score in ranked:
            prob = score / total_score
            prob = prob * 10.0
            
            original_name = display_to_original.get(song_name, song_name)
            if original_name not in song_data and song_name in song_data:
                original_name = song_name
            
            data = song_data.get(original_name, {})
            
            spotify_track_id = None
            if original_name in spotify_data:
                spotify_track_id = spotify_data[original_name].get("id")
            elif song_name in spotify_data:
                spotify_track_id = spotify_data[song_name].get("id")
            elif song_name in all_spotify:
                spotify_track_id = all_spotify[song_name].get("id")
            
            predictions.append(
                SongPrediction(
                    title=song_name,
                    probability=round(prob, 4),
                    appearances=data.get("count", 0),
                    weighted_appearances=round(data.get("weighted_count", 0.0), 3),
                    typical_position=int(median(data.get("positions", []))) if data.get("positions") else None,
                    last_seen=data.get("last_seen"),
                    spotify_track_id=spotify_track_id,
                )
            )



        return PredictionSummary(
            artist_mbid=artist_mbid,
            tour=None,
            sets_considered=total_shows,
            effective_shows=round(total_weight, 3),
            unique_songs=len(song_data),
            songs=predictions,
            model_name="simple_recency_v1",
            model_params={
                "half_life_days": config.half_life_days,
                "top_k": config.top_k,
                "spotify_recency_boost": config.spotify_recency_boost,
                "spotify_popularity_weight": config.spotify_popularity_weight,
                "spotify_top_track_boost": config.spotify_top_track_boost,
            },
            meta=meta,
        )