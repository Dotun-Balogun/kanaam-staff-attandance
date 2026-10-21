// Builds the sidebar on every page, so it is never copy-pasted.
import { initScannerStatus } from "./scanner-status.js";

const LINKS = [
  ["index.html", "clock", "Clock"],
  ["dashboard.html", "dashboard", "Dashboard"],
  ["staff.html", "staff", "Staff"],
  ["reports.html", "reports", "Reports"],
  ["settings.html", "settings", "Settings"],
];

export function mountSidebar() {
  const page = document.body.dataset.page;
  const el = document.getElementById("sidebar");
  el.className = "sidebar";
  el.innerHTML = `
    <div class="brand">
      <p class="brand-title">Kanam Local Government<br>Secretariat, Plateau State</p>
      <p class="brand-sub">Biometric Staff Attendance</p>
    </div>
    <nav class="nav" aria-label="Main">
      ${LINKS.map(([href, id, label]) => `<a href="${href}"${id === page ? ' aria-current="page"' : ""}>${label}</a>`).join("")}
    </nav>
    <div class="hw"><i></i><span>Checking scanner…</span></div>`;
  initScannerStatus(el.querySelector(".hw"));
}
