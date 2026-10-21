import { mountSidebar } from "../components/sidebar.js";
import { get, apiUrl } from "../api.js";
import { $, esc, table, options, badge } from "../utils.js";

mountSidebar();

async function load() {
  const q = `?start=${$("#from").value}&end=${$("#to").value}&department_id=${$("#dept").value || 0}`;
  const rows = await get("/reports" + q);
  $("#export").href = apiUrl("/reports/export.csv" + q);
  $("#summary").textContent = `${rows.length} record${rows.length === 1 ? "" : "s"} · ${rows.filter((r) => r.status === "Late").length} late`;
  $("#rows").innerHTML = table(["Date", "Name", "Staff no", "Department", "In", "Out", "Hours", "Status"],
    rows.map((r) => [esc(r.date), esc(r.name), esc(r.staff_no), esc(r.department), esc(r.clock_in), esc(r.clock_out || "-"), esc(r.hours === "" ? "-" : r.hours), badge(r.status)]));
}
(async () => {
  try {
    $("#dept").innerHTML = options(await get("/departments"), (d) => d.name, "All departments");
    $("#from").onchange = $("#to").onchange = $("#dept").onchange = load;
    load();
  } catch (e) { $("#rows").textContent = e.message; }
})();
