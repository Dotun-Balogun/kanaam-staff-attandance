"""Scanner access. Every operation runs in a fresh worker process (see worker.py),
because the scanner re-enumerates on USB after each use and libfprint cannot be
re-initialised inside one long-running process."""
import base64, glob, json, subprocess, sys, threading, time
from pathlib import Path

WORKER = Path(__file__).with_name("worker.py")
_lock = threading.Lock()


def available() -> bool:
    """Checks the system USB list only."""
    for f in glob.glob("/sys/bus/usb/devices/*/idVendor"):
        try:
            if open(f).read().strip() == "05ba":
                return True
        except OSError:
            pass
    return False


def _run(args, payload=None, timeout=120):
    last = "Scanner process failed"
    for _ in range(3):
        try:
            p = subprocess.run([sys.executable, str(WORKER), *args], input=payload,
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timed out waiting for a thumb")
        line = next((l for l in reversed(p.stdout.splitlines()) if l.startswith("RESULT:")), None)
        if line:
            r = json.loads(line[7:])
            if "error" not in r:
                return r
            last = r["error"]
            if not r.get("retry"):
                break
        else:
            last = (p.stderr.strip().splitlines() or [last])[-1]
        time.sleep(1.5)  # let the scanner re-appear on USB, then try again
    raise RuntimeError(last)


def enroll(label: str) -> bytes:
    with _lock:
        return base64.b64decode(_run(["enroll", label])["template"])


def identify(templates: list):
    with _lock:
        payload = json.dumps([base64.b64encode(t).decode() for t in templates])
        return _run(["identify"], payload, timeout=90)["index"]
