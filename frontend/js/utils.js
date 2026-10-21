export const $ = (s) => document.querySelector(s);
export const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function table(headers, rows) {
  if (!rows.length) return '<div class="empty">Nothing here yet.</div>';
  const head = headers.map((h) => `<th>${h}</th>`).join("");
  const body = rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("");
  return `<div class="table-wrap"><table><tr>${head}</tr>${body}</table></div>`;
}
export function say(el, text, kind = "") { el.textContent = text; el.className = "msg " + kind; }
export function courseOptions(courses, all = false) {
  const opts = courses.map((c) => `<option value="${c.id}">${esc(c.code)} · ${esc(c.title)}</option>`).join("");
  return (all ? '<option value="0">All courses</option>' : "") + (opts || (all ? "" : '<option value="">Add a course first</option>'));
}

export function options(list, label, all = "") {
  const opts = list.map((x) => `<option value="${x.id}">${esc(label(x))}</option>`).join("");
  return (all ? `<option value="0">${all}</option>` : "") + opts;
}
export const badge = (status) => `<span class="badge ${status === "Late" ? "late" : "ok"}">${esc(status)}</span>`;
