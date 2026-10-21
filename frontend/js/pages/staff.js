import { mountSidebar } from "../components/sidebar.js";
import { get, post, del } from "../api.js";
import { $, esc, table, say, options } from "../utils.js";

mountSidebar();

async function load() {
  $("#dept").innerHTML = options(await get("/departments"), (d) => d.name) || '<option value="">Add a department in Settings</option>';
  const s = await get("/staff");
  $("#list").innerHTML = table(["Name", "Staff no", "Department", "Designation", ""],
    s.map((x) => [esc(x.name), esc(x.staff_no), esc(x.department || ""), esc(x.designation || ""), `<button class="btn ghost" data-id="${x.id}">Remove</button>`]));
  document.querySelectorAll("[data-id]").forEach((b) => (b.onclick = async () => {
    if (confirm("Remove this staff member and their attendance records?")) { await del("/staff/" + b.dataset.id); load(); }
  }));
}
$("#reg").onclick = async () => {
  const btn = $("#reg"), msg = $("#reg-msg");
  btn.disabled = true;
  say(msg, "Press the thumb on the scanner 5 times…");
  try {
    await post("/staff", { staff_no: $("#no").value, name: $("#name").value, department_id: +$("#dept").value || 0, designation: $("#desig").value });
    say(msg, "Registered. This staff member can now clock in.", "good");
    $("#no").value = $("#name").value = $("#desig").value = "";
    load();
  } catch (e) { say(msg, e.message, "err"); }
  btn.disabled = false;
};
load().catch((e) => say($("#reg-msg"), e.message, "err"));
