// Every backend call lives here.
import { API_BASE } from "./config.js";

export async function api(path, opts = {}) {
  let r;
  try {
    r = await fetch(API_BASE + "/api" + path, { headers: { "Content-Type": "application/json" }, ...opts });
  } catch {
    throw new Error("Cannot reach the scanner backend. Is ./run.sh running on this laptop?");
  }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
}
export const get = (p) => api(p);
export const post = (p, body) => api(p, { method: "POST", body: JSON.stringify(body || {}) });
export const del = (p) => api(p, { method: "DELETE" });
export const apiUrl = (p) => API_BASE + "/api" + p;
