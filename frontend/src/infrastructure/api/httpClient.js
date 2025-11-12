import { API_BASE } from "./config";

async function request(path, params = {}) {
    const url = new URL(path, API_BASE);
    Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") return;
        url.searchParams.set(key, String(value));
    });

    const response = await fetch(url.toString());
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