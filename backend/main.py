import csv, io, os, re, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import scanner

BASE = Path(__file__).parent
STAFF_NO = re.compile(r"^[A-Za-z0-9/\-]{2,30}$")
DEFAULTS = {"work_start": "08:00", "work_end": "16:00", "grace_minutes": "15"}
app = FastAPI(title="Biometric Staff Attendance")

# Hosted UI (Vercel / Netlify) may call this local backend. Custom domain: set ALLOWED_ORIGIN_REGEX.
ORIGIN_RE = os.getenv("ALLOWED_ORIGIN_REGEX", r"https://.*\.(vercel\.app|netlify\.app)|http://(localhost|127\.0\.0\.1)(:\d+)?")
app.add_middleware(CORSMiddleware, allow_origin_regex=ORIGIN_RE, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def private_network(request, call_next):
    resp = await call_next(request)  # Chrome asks permission before an https site calls localhost
    if request.headers.get("access-control-request-private-network"):
        resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp


def db():
    c = sqlite3.connect(BASE / "staff.db")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


with db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS departments(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
    CREATE TABLE IF NOT EXISTS staff(id INTEGER PRIMARY KEY, staff_no TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        department_id INTEGER REFERENCES departments(id), designation TEXT, template BLOB NOT NULL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff(id),
        work_date TEXT NOT NULL, clock_in TEXT, clock_out TEXT, status TEXT, UNIQUE(staff_id, work_date));
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    """)


def cfg(c):
    d = dict(DEFAULTS)
    d.update({r["key"]: r["value"] for r in c.execute("SELECT key,value FROM settings")})
    return d


def hm(iso):
    return datetime.fromisoformat(iso).strftime("%I:%M %p") if iso else ""


def hours(a, b):
    return round((datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 3600, 2) if a and b else ""


class DeptIn(BaseModel):
    name: str


class StaffIn(BaseModel):
    staff_no: str
    name: str
    department_id: int
    designation: str = ""


class SettingsIn(BaseModel):
    work_start: str
    work_end: str
    grace_minutes: int


@app.get("/api/health")
def health():
    try:
        return {"scanner": scanner.available()}
    except Exception:
        return {"scanner": False}


# ---------- settings & departments ----------
@app.get("/api/settings")
def get_settings():
    with db() as c:
        return cfg(c)


@app.put("/api/settings")
def put_settings(b: SettingsIn):
    try:
        datetime.strptime(b.work_start, "%H:%M"); datetime.strptime(b.work_end, "%H:%M")
    except ValueError:
        raise HTTPException(400, "Use the time format HH:MM")
    if not 0 <= b.grace_minutes <= 120:
        raise HTTPException(400, "Grace period must be 0 to 120 minutes")
    with db() as c:
        for k, v in b.dict().items():
            c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, str(v)))
    return {"ok": True}


@app.get("/api/departments")
def departments():
    with db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM departments ORDER BY name")]


@app.post("/api/departments")
def add_department(b: DeptIn):
    try:
        with db() as c:
            c.execute("INSERT INTO departments(name) VALUES(?)", (b.name.strip(),))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Department already exists")
    return {"ok": True}


@app.delete("/api/departments/{did}")
def remove_department(did: int):
    with db() as c:
        if c.execute("SELECT 1 FROM staff WHERE department_id=?", (did,)).fetchone():
            raise HTTPException(409, "Remove or move the staff in this department first")
        c.execute("DELETE FROM departments WHERE id=?", (did,))
    return {"ok": True}


# ---------- staff ----------
@app.post("/api/staff")
def register(b: StaffIn):
    no = b.staff_no.strip().upper()
    if not STAFF_NO.match(no):
        raise HTTPException(400, "Staff number may contain letters, numbers, / and - only")
    if not b.name.strip():
        raise HTTPException(400, "Name is required")
    with db() as c:
        if c.execute("SELECT 1 FROM staff WHERE staff_no=?", (no,)).fetchone():
            raise HTTPException(409, "This staff number is already registered")
        if not c.execute("SELECT 1 FROM departments WHERE id=?", (b.department_id,)).fetchone():
            raise HTTPException(400, "Choose a department (add one in Settings first)")
    try:
        template = scanner.enroll(no)
    except Exception as e:
        raise HTTPException(500, f"Scanner error: {e}")
    with db() as c:
        c.execute("INSERT INTO staff(staff_no,name,department_id,designation,template,created_at) VALUES(?,?,?,?,?,?)",
                  (no, b.name.strip().title(), b.department_id, b.designation.strip(), template, datetime.now().isoformat(timespec="seconds")))
    return {"ok": True}


@app.get("/api/staff")
def staff_list():
    with db() as c:
        return [dict(r) for r in c.execute("""SELECT s.id,s.staff_no,s.name,s.designation,d.name AS department
            FROM staff s LEFT JOIN departments d ON d.id=s.department_id ORDER BY s.name""")]


@app.delete("/api/staff/{sid}")
def remove_staff(sid: int):
    with db() as c:
        c.execute("DELETE FROM attendance WHERE staff_id=?", (sid,))
        c.execute("DELETE FROM staff WHERE id=?", (sid,))
    return {"ok": True}


# ---------- clock in / out ----------
@app.post("/api/clock")
def clock():
    """Waits for a thumb. First scan of the day = clock in, next scan = clock out."""
    with db() as c:
        rows = c.execute("""SELECT s.id,s.staff_no,s.name,s.designation,s.template,d.name AS department
            FROM staff s LEFT JOIN departments d ON d.id=s.department_id""").fetchall()
        settings = cfg(c)
    if not rows:
        raise HTTPException(400, "No staff registered yet")
    try:
        idx = scanner.identify([r["template"] for r in rows])
    except Exception as e:
        raise HTTPException(500, f"Scanner error: {e}")
    if idx is None:
        return {"action": "unknown", "message": "Fingerprint not recognised. Please see the administrator to register."}
    s, t = rows[idx], datetime.now()
    who = {"name": s["name"], "staff_no": s["staff_no"], "designation": s["designation"], "department": s["department"]}
    day = t.date().isoformat()
    with db() as c:
        rec = c.execute("SELECT * FROM attendance WHERE staff_id=? AND work_date=?", (s["id"], day)).fetchone()
        if rec is None:
            limit = datetime.combine(t.date(), datetime.strptime(settings["work_start"], "%H:%M").time()) + timedelta(minutes=int(settings["grace_minutes"]))
            status = "Late" if t > limit else "On time"
            c.execute("INSERT INTO attendance(staff_id,work_date,clock_in,status) VALUES(?,?,?,?)",
                      (s["id"], day, t.isoformat(timespec="seconds"), status))
            return {"action": "in", "status": status, "time": hm(t.isoformat()), **who}
        if rec["clock_out"] is None:
            if t - datetime.fromisoformat(rec["clock_in"]) < timedelta(minutes=2):
                return {"action": "duplicate", "time": hm(rec["clock_in"]), **who}
            c.execute("UPDATE attendance SET clock_out=? WHERE id=?", (t.isoformat(timespec="seconds"), rec["id"]))
            return {"action": "out", "time": hm(t.isoformat()), "hours": hours(rec["clock_in"], t.isoformat()), **who}
    return {"action": "done", "time_in": hm(rec["clock_in"]), "time_out": hm(rec["clock_out"]), **who}


# ---------- dashboard & reports ----------
@app.get("/api/dashboard")
def dashboard():
    day = datetime.now().date().isoformat()
    with db() as c:
        total = c.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
        today = c.execute("""SELECT a.*,s.staff_no,s.name,d.name AS department FROM attendance a JOIN staff s ON s.id=a.staff_id
            LEFT JOIN departments d ON d.id=s.department_id WHERE a.work_date=? ORDER BY a.clock_in DESC""", (day,)).fetchall()
        absent = c.execute("""SELECT s.staff_no,s.name,d.name AS department FROM staff s LEFT JOIN departments d ON d.id=s.department_id
            WHERE s.id NOT IN (SELECT staff_id FROM attendance WHERE work_date=?) ORDER BY s.name""", (day,)).fetchall()
    return {"total": total, "present": len(today), "late": sum(1 for r in today if r["status"] == "Late"),
            "clocked_out": sum(1 for r in today if r["clock_out"]), "absent": [dict(r) for r in absent],
            "today": [{"name": r["name"], "staff_no": r["staff_no"], "department": r["department"], "status": r["status"],
                       "clock_in": hm(r["clock_in"]), "clock_out": hm(r["clock_out"])} for r in today]}


def _report(start, end, dept):
    q = """SELECT a.work_date,a.clock_in,a.clock_out,a.status,s.staff_no,s.name,s.designation,d.name AS department
           FROM attendance a JOIN staff s ON s.id=a.staff_id LEFT JOIN departments d ON d.id=s.department_id WHERE 1=1"""
    p = []
    if start: q += " AND a.work_date>=?"; p.append(start)
    if end: q += " AND a.work_date<=?"; p.append(end)
    if dept: q += " AND s.department_id=?"; p.append(dept)
    with db() as c:
        rows = c.execute(q + " ORDER BY a.work_date DESC, s.name", p).fetchall()
    return [{"date": r["work_date"], "staff_no": r["staff_no"], "name": r["name"], "department": r["department"] or "",
             "designation": r["designation"] or "", "clock_in": hm(r["clock_in"]), "clock_out": hm(r["clock_out"]),
             "status": r["status"], "hours": hours(r["clock_in"], r["clock_out"])} for r in rows]


@app.get("/api/reports")
def reports(start: str = "", end: str = "", department_id: int = 0):
    return _report(start, end, department_id)


@app.get("/api/reports/export.csv")
def export(start: str = "", end: str = "", department_id: int = 0):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Date", "Staff No", "Name", "Department", "Designation", "Clock in", "Clock out", "Status", "Hours"])
    for r in _report(start, end, department_id):
        w.writerow([r["date"], r["staff_no"], r["name"], r["department"], r["designation"], r["clock_in"], r["clock_out"], r["status"], r["hours"]])
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=staff-attendance.csv"})


app.mount("/", StaticFiles(directory=BASE.parent / "frontend", html=True), name="ui")
