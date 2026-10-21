# Biometric Staff Attendance Management System
Kanam Local Government Area Secretariat, Plateau State.
Stack: **Python (FastAPI) + SQLite + libfprint** backend, **plain HTML/CSS/JS** frontend (no build step).

## Features
- **Enrol** staff (staff number, name, department, designation) with 5 thumb scans
- **Clock in / out** with one thumb: first scan of the day clocks in, the next clocks out
- **Late detection** from resumption time plus a grace period (set in Settings)
- **Dashboard:** present, late, not-yet-in, today's activity (auto-refresh)
- **Reports** by date and department, hours worked, CSV export
- **Departments** and working hours managed in Settings

## Structure
```
backend/   main.py (API, database, clock logic)  scanner.py + worker.py (scanner access)
frontend/  <- host this folder
  index.html (clock) dashboard.html staff.html reports.html settings.html
  css/   base.css  layout.css  components.css  pages/clock.css
  js/    config.js  api.js  utils.js  components/ (sidebar, scanner-status)  pages/ (one per screen)
```
Add a page: new `.html` + `js/pages/<name>.js` + one line in `js/components/sidebar.js`.

## Setup (one time, Linux)
```bash
sudo apt install -y fprintd libfprint-2-2 gir1.2-fprint-2.0 python3-gi python3-pip usbutils
lsusb                                   # look for 05ba:000a (DigitalPersona U.are.U)
sudo cp 99-fingerprint.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger   # then replug the scanner
pip3 install --user -r backend/requirements.txt
```
(If pip says "externally managed environment", add `--break-system-packages`.)

## First use
1. `./run.sh`, then open http://localhost:8000
2. **Settings:** add departments, set resumption/closing time and grace period
3. **Staff:** register each person
4. **Clock:** leave this page open on the scanner laptop

## Host the UI (Netlify / Vercel)
Publish the `frontend` folder (no build command). Run `./run.sh` on the scanner laptop and open the hosted link
in Chrome or Edge, accepting the local-network prompt. `js/config.js` points hosted copies at `http://localhost:8000`.
Custom domain: `ALLOWED_ORIGIN_REGEX='https://my\.domain\.com' ./run.sh`.

## Troubleshooting
Scanner not found: replug, check `lsusb`. Access denied: redo the udev step. First scan fails: retry.
Warnings about `power/persist` / `libusb_exit` are harmless. Changing scanner model means re-registering everyone.

## Limitations
- Runs on the laptop the scanner is plugged into (a cloud server cannot read a local USB port).
- "Not yet in" counts every registered staff member, so weekends and public holidays show everyone as absent.
- Templates created with libfprint cannot be used with the Windows DigitalPersona SDK.
