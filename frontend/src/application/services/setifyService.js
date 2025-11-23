import { createArtist, createPrediction, createSetlist } from "../../domain/models";
import { fetchPrediction, fetchSetlists, searchArtist } from "../../infrastructure/api/setifyGateway";

export async function findArtistByName(name) {
    const artist = await searchArtist(name);
    return createArtist(artist);
}

export async function loadSetlists({ mbid, pages }) {
    const response = await fetchSetlists({ mbid, pages });
    return {
        meta: response.meta ?? {},
        setlists: Array.isArray(response.setlists)
            ? response.setlists.map((setlist) => createSetlist(setlist))
            : [],
    };
}

export async function predictSetlist({ mbid, pages }) {
    const prediction = await fetchPrediction({
        mbid,
        pages,
    });
    return createPrediction(prediction);
}