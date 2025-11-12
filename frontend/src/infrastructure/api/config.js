const RAW_BASE = import.meta.env?.VITE_API_BASE || "http://127.0.0.1:8000";
export const API_BASE = RAW_BASE.replace(/\/$/, "");