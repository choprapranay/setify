import { track } from "@vercel/analytics/react";
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
    let prediction;
    try {
        track("predict_route_called", { mbid, pages });
        prediction = await fetchPrediction({
            mbid,
            pages,
        });
        track("predict_route_succeeded", { mbid, pages });
    } catch (error) {
        track("predict_route_failed", {
            mbid,
            pages,
            reason: error?.message?.slice(0, 120) ?? "unknown",
        });
        throw error;
    }
    return createPrediction(prediction);
}