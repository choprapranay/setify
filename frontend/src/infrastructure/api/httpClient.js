import { API_BASE } from "./config";

async function request(path, params = {}) {
    const normalized = path.replace(/^\//, "");

    const url = new URL(`${API_BASE}/${normalized}`);

    Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") return;
        url.searchParams.set(key, String(value));
    });

    console.log("[FETCH]", url.toString());

    const response = await fetch(url.toString(), {
        method: "GET",
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const detail = data?.detail || `${response.status} ${response.statusText}`;
        throw new Error(detail);
    }

    return data;
}

export const httpClient = {
    get: request,
};
