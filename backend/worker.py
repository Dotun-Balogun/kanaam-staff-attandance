"""One-shot scanner process. Usage: worker.py enroll LABEL | worker.py identify (templates on stdin)."""
import sys, json, base64
import gi
gi.require_version("FPrint", "2.0")
from gi.repository import FPrint


def out(d):
    print("RESULT:" + json.dumps(d), flush=True)


ctx = FPrint.Context()
devs = ctx.get_devices()
if not devs:
    out({"error": "Scanner not found. Replug the USB.", "retry": True})
    sys.exit(0)
dev = devs[0]
try:
    dev.open_sync()
except Exception as e:
    out({"error": str(e), "retry": True})
    sys.exit(0)

try:
    if sys.argv[1] == "enroll":
        t = FPrint.Print.new(dev)
        t.set_finger(FPrint.Finger.RIGHT_THUMB)
        t.set_username(sys.argv[2])
        p = dev.enroll_sync(t, None, None, None)
        out({"template": base64.b64encode(bytes(p.serialize())).decode()})
    else:
        raw = json.load(sys.stdin)
        gallery = [FPrint.Print.deserialize(base64.b64decode(x)) for x in raw]
        match, _ = dev.identify_sync(gallery, None, None, None)
        idx = None
        if match is not None:
            for i, g in enumerate(gallery):
                if g.equal(match):
                    idx = i
                    break
        out({"index": idx})
except Exception as e:
    out({"error": str(e)})
finally:
    try:
        dev.close_sync()
    except Exception:
        pass
