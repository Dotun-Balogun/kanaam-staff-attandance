import { mountSidebar } from "../components/sidebar.js";
import { post } from "../api.js";
import { $, esc, sleep } from "../utils.js";

mountSidebar();
let running = true;

function tick() {
  const n = new Date();
  $("#time").textContent = n.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  $("#date").textContent = n.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}
setInterval(tick, 1000); tick();

function card(cls, title, body) { return `<div class="res ${cls}"><b>${esc(title)}</b>${body}</div>`; }

function show(r) {
  const who = `${esc(r.designation || "")}${r.designation && r.department ? " · " : ""}${esc(r.department || "")}`;
  if (r.action === "unknown") return card("unknown", "Not recognised", esc(r.message));
  if (r.action === "in") return card(r.status === "Late" ? "late" : "ok", r.name, `${who}<br>Clocked in at ${esc(r.time)} · ${esc(r.status)}`);
  if (r.action === "out") return card("ok", r.name, `${who}<br>Clocked out at ${esc(r.time)}<br>Hours worked: ${esc(r.hours)}`);
  if (r.action === "duplicate") return card("duplicate", r.name, `Already clocked in at ${esc(r.time)}`);
  return card("duplicate", r.name, `Already completed today (in ${esc(r.time_in)}, out ${esc(r.time_out)})`);
}

async function loop() {
  for (;;) {
    if (!running) { await sleep(500); continue; }
    $("#pad").classList.add("wait");
    $("#pad-text").textContent = "Place your thumb on the scanner";
    try {
      const r = await post("/clock");
      $("#pad").classList.remove("wait");
      $("#result").innerHTML = show(r);
    } catch (e) {
      $("#pad").classList.remove("wait");
      $("#result").innerHTML = card("error", "Scan problem", esc(e.message));
    }
    await sleep(2200);
  }
}
$("#toggle").onclick = () => {
  running = !running;
  $("#toggle").textContent = running ? "Pause terminal" : "Resume terminal";
  if (!running) { $("#pad").classList.remove("wait"); $("#pad-text").textContent = "Terminal paused"; }
};
loop();
