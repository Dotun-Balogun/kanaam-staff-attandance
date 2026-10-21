// The ONE place to point the UI at the backend.
// Served by FastAPI (port 8000): same origin. Hosted anywhere else: the backend on your laptop.
export const API_BASE = location.port === "8000" ? "" : "http://localhost:8000";
