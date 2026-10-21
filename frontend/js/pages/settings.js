import { mountSidebar } from "../components/sidebar.js";
import { api, get, post, del } from "../api.js";
import { $, esc, table, say } from "../utils.js";

mountSidebar();

async function load() {
  const s = await get("/settings");
  $("#start").value = s.work_start; $("#end").value = s.work_end; $("#grace").value = s.grace_minutes;
  const d = await get("/departments");
  $("#depts").innerHTML = table(["Department", ""], d.map((x) => [esc(x.name), `<button class="btn ghost" data-id="${x.id}">Remove</button>`]));
  document.querySelectorAll("[data-id]").forEach((b) => (b.onclick = async () => {
    try { await del("/departments/" + b.dataset.id); load(); } catch (e) { say($("#dept-msg"), e.message, "err"); }
  }));
}
$("#save").onclick = async () => {
  try {
    await api("/settings", { method: "PUT", body: JSON.stringify({ work_start: $("#start").value, work_end: $("#end").value, grace_minutes: +$("#grace").value }) });
    say($("#hours-msg"), "Saved.", "good");
  } catch (e) { say($("#hours-msg"), e.message, "err"); }
};
$("#add").onclick = async () => {
  try { await post("/departments", { name: $("#dname").value }); $("#dname").value = ""; say($("#dept-msg"), "Department added.", "good"); load(); }
  catch (e) { say($("#dept-msg"), e.message, "err"); }
};
load().catch((e) => say($("#hours-msg"), e.message, "err"));
