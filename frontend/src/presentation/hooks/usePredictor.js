import { useCallback, useMemo, useState } from "react";

import { findArtistByName, predictSetlist } from "../../application/services/setifyService";

const FIRST_VISIT_NOTICE_KEY = "setify:first-visit-notice";

const formatNumber = (value, digits = 0) =>
    new Intl.NumberFormat(undefined, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
    }).format(value ?? 0);

export function usePredictor() {
    const [artistQuery, setArtistQueryState] = useState("");
    const [artist, setArtist] = useState(null);

    const [prediction, setPrediction] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [firstVisitNotice, setFirstVisitNotice] = useState("");

    const [sortState, setSortState] = useState(["prob", "desc"]);
    const [hasSeenColdStartNotice, setHasSeenColdStartNotice] = useState(() => {
        if (typeof window === "undefined") return true;
        return window.localStorage.getItem(FIRST_VISIT_NOTICE_KEY) === "true";
    });

    const canPredict = artistQuery.trim().length > 1;

    const setArtistQuery = useCallback((value) => {
        setArtistQueryState(value);
        setError(null);
        if (!value.trim()) {
            setArtist(null);
            setPrediction(null);
        }
    }, []);

    const predict = useCallback(async () => {
        if (!canPredict) {
            setError("Enter at least two characters.");
            return;
        }
        if (hasSeenColdStartNotice) {
            setFirstVisitNotice("");
        }
        if (!hasSeenColdStartNotice) {
            const notice =
                "Heads up: the Render backend can take up to ~50 seconds to spin up on the first run. Thanks for your patience!";
            setFirstVisitNotice(notice);
            setHasSeenColdStartNotice(true);
            if (typeof window !== "undefined") {
                window.localStorage.setItem(FIRST_VISIT_NOTICE_KEY, "true");
            }
        }
        setLoading(true);
        setError(null);
        setPrediction(null);
        setArtist(null);
        try {
            const result = await findArtistByName(artistQuery.trim());
            if (!result) {
                throw new Error("Artist not found");
            }
            setArtist(result);
            
            const predictionResult = await predictSetlist({
                mbid: result.mbid,
                pages: 5,
            });
            setPrediction(predictionResult);
        } catch (err) {
            setArtist(null);
            setError(err.message || String(err));
        } finally {
            setLoading(false);
        }
    }, [artistQuery, canPredict, hasSeenColdStartNotice]);

    const sortedSongs = useMemo(() => {
        if (!prediction?.songs?.length) return [];
        const [sortKey, sortDir] = sortState;
        const sorted = [...prediction.songs];
        sorted.sort((a, b) => {
            let va = 0;
            let vb = 0;
            switch (sortKey) {
                case "prob":
                    va = a.probability;
                    vb = b.probability;
                    break;
                case "apps":
                    va = a.appearances;
                    vb = b.appearances;
                    break;
                case "pos":
                    va = a.typicalPosition ?? Infinity;
                    vb = b.typicalPosition ?? Infinity;
                    break;
                default:
                    va = a.title.toLowerCase();
                    vb = b.title.toLowerCase();
            }
            if (va < vb) return sortDir === "asc" ? -1 : 1;
            if (va > vb) return sortDir === "asc" ? 1 : -1;
            return 0;
        });
        return sorted;
    }, [prediction, sortState]);

    const toggleSort = useCallback((key) => {
        setSortState(([currentKey, direction]) => {
            if (currentKey === key) {
                return [key, direction === "asc" ? "desc" : "asc"];
            }
            return [key, "desc"];
        });
    }, []);

    return {
        state: {
            artistQuery,
            artist,
            prediction,
            error,
            loading,
            sortedSongs,
            sortKey: sortState[0],
            sortDir: sortState[1],
            canPredict,
            formatNumber,
            firstVisitNotice,
        },
        actions: {
            setArtistQuery,
            predict,
            toggleSort,
        },
    };
}