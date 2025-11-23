export function createArtist(payload) {
    if (!payload) return null;
    return {
        name: payload.name ?? "",
        mbid: payload.mbid ?? "",
    };
}

export function createSetlist(payload) {
    if (!payload) return null;
    return {
        id: payload.id ?? "",
        eventDate: payload.event_date ?? null,
        tour: payload.tour ?? null,
        songs: Array.isArray(payload.songs)
            ? payload.songs.map((song) => ({
                title: song.title ?? "",
                position: song.position ?? null,
            }))
            : [],
    };
}

export function createPrediction(payload) {
    if (!payload) return null;
    return {
        model: payload.model ?? {},
        artistMbid: payload.artist_mbid ?? "",
        tour: payload.tour ?? null,
        setsConsidered: payload.sets_considered ?? 0,
        effectiveShows: payload.effective_shows ?? 0,
        uniqueSongs: payload.unique_songs ?? 0,
        meta: payload.meta ?? {},
        confidence: payload.confidence ?? 0,
        songs: Array.isArray(payload.songs)
            ? payload.songs.map((song) => ({
                title: song.title ?? "",
                probability: song.probability ?? 0,
                appearances: song.appearances ?? 0,
                weightedAppearances: song.weighted_appearances ?? 0,
                typicalPosition: song.typical_position ?? null,
                lastSeen: song.last_seen ?? null,
                spotifyTrackId: song.spotify_track_id ?? null,
            }))
            : [],
    };
}