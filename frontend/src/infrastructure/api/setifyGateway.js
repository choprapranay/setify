import { httpClient } from "./httpClient";

export async function searchArtist(query) {
    return httpClient.get("/api/artist", { artist: query });
}

export async function fetchSetlists({ mbid, pages }) {
    return httpClient.get("/api/setlists", { mbid, pages });
}

export async function fetchPrediction({
                                          mbid,
                                          pages,
                                          tour,
                                          topK,
                                          halfLifeDays,
                                          alpha,
                                          beta,
                                      }) {
    return httpClient.get("/api/predict", {
        mbid,
        pages,
        tour,
        top_k: topK,
        half_life_days: halfLifeDays,
        alpha,
        beta,
    });
}