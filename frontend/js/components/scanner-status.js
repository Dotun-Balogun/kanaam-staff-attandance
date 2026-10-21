import { get } from "../api.js";

export function initScannerStatus(el) {
  const label = el.querySelector("span");
  async function check() {
    try {
      const h = await get("/health");
      el.classList.toggle("up", h.scanner);
      label.textContent = h.scanner ? "Scanner connected" : "Scanner not found";
    } catch {
      el.classList.remove("up");
      label.textContent = "Backend offline";
    }
  }
  check();
  setInterval(check, 4000);
}
