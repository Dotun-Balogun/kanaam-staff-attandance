import { mountSidebar } from "../components/sidebar.js";
import { get } from "../api.js";
import { $, esc, table, badge } from "../utils.js";

mountSidebar();

async function load() {
  try {
    const d = await get("/dashboard");
    $("#s-total").textContent = d.total;
    $("#s-present").textContent = d.present;
    $("#s-late").textContent = d.late;
    $("#s-absent").textContent = d.absent.length;
    $("#today").innerHTML = table(["Name", "Staff no", "Department", "In", "Out", "Status"],
      d.today.map((r) => [esc(r.name), esc(r.staff_no), esc(r.department || ""), esc(r.clock_in), esc(r.clock_out || "-"), badge(r.status)]));
    $("#absent").innerHTML = table(["Name", "Staff no", "Department"],
      d.absent.map((r) => [esc(r.name), esc(r.staff_no), esc(r.department || "")]));
  } catch (e) { $("#today").textContent = e.message; }
}
load(); setInterval(load, 15000);
