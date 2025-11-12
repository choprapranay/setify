import { useCallback, useMemo, useState } from "react";

import { findArtistByName, loadSetlists, predictSetlist } from "../../application/services/setifyService";

const formatNumber = (value, digits = 0) =>
    new Intl.NumberFormat(undefined, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
    }).format(value ?? 0);

export function usePredictor() {
    const [artistQuery, setArtistQuery] = useState("");
    const [artist, setArtist] = useState(null);
    const [tours, setTours] = useState([]);
    const [selectedTour, setSelectedTour] = useState(null);

    const [pages, setPages] = useState(5);
    const [topK, setTopK] = useState(20);
    const [halfLife, setHalfLife] = useState(180);
    const [alpha, setAlpha] = useState(1);
    const [beta, setBeta] = useState(1);

    const [prediction, setPrediction] = useState(null);
    const [error, setError] = useState(null);
    const [loadingArtist, setLoadingArtist] = useState(false);
    const [loadingPrediction, setLoadingPrediction] = useState(false);

    const [sortState, setSortState] = useState(["prob", "desc"]);

    const canSearch = artistQuery.trim().length > 1;

    const findTours = useCallback(async (mbid) => {
        try {
            const { setlists } = await loadSetlists({ mbid, pages: 3 });
            const uniqueTours = Array.from(
                new Set(setlists.map((setlist) => setlist.tour).filter(Boolean))
            ).sort();
            setTours(uniqueTours);
        } catch {
            setTours([]);
        }
    }, []);

    const search = useCallback(async () => {
        if (!canSearch) return;
        setLoadingArtist(true);
        setError(null);
        setPrediction(null);
        setTours([]);
        setSelectedTour(null);
        try {
            const result = await findArtistByName(artistQuery.trim());
            if (!result) {
                throw new Error("Artist not found");
            }
            setArtist(result);
            findTours(result.mbid);
        } catch (err) {
            setArtist(null);
            setError(err.message || String(err));
        } finally {
            setLoadingArtist(false);
        }
    }, [artistQuery, canSearch, findTours]);

    const predict = useCallback(async () => {
        if (!artist) {
            setError("Pick an artist first.");
            return;
        }
        setLoadingPrediction(true);
        setError(null);
        setPrediction(null);
        try {
            const result = await predictSetlist({
                mbid: artist.mbid,
                pages,
                tour: selectedTour,
                topK,
                halfLifeDays: halfLife,
                alpha,
                beta,
            });
            setPrediction(result);
        } catch (err) {
            setError(err.message || String(err));
        } finally {
            setLoadingPrediction(false);
        }
    }, [artist, pages, selectedTour, topK, halfLife, alpha, beta]);

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
            tours,
            selectedTour,
            pages,
            topK,
            halfLife,
            alpha,
            beta,
            prediction,
            error,
            loadingArtist,
            loadingPrediction,
            sortedSongs,
            sortKey: sortState[0],
            sortDir: sortState[1],
            canSearch,
            formatNumber,
        },
        actions: {
            setArtistQuery,
            setSelectedTour,
            setPages,
            setTopK,
            setHalfLife,
            setAlpha,
            setBeta,
            search,
            predict,
            toggleSort,
        },
    };
}