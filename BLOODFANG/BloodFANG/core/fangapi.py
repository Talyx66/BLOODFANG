# fangapi.py
"""
API discovery:
 - discover_api_endpoints(base, emit, stop_event=None)
 - run(target, emit, stop_event=None)  # target = base URL
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

ENDPOINTS = _load_payloads("api_endpoints.txt", ["/api/", "/api/v1/", "/v1/", "/graphql"])

def discover_api_endpoints(base, emit, stop_event=None):
    if not base:
        emit("[API] Missing base URL.")
        return
    emit(f"[API] Starting discovery on {base}")
    for ep in ENDPOINTS:
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            emit("[API] Stopped by user.")
            return
        url = base.rstrip("/") + ep
        try:
            r = requests.get(url, timeout=6, verify=False)
            emit(f"[API] {r.status_code} {url}")
            if r.status_code == 200:
                emit(f"[API] Found endpoint: {url}")
        except requests.exceptions.RequestException as re:
            emit(f"[API] Request error: {re}")
        except Exception as e:
            emit(f"[API] Unexpected error: {e}")
        time.sleep(0.25)
    emit("[API] Complete.")

def run(target, emit, stop_event=None):
    discover_api_endpoints(target, emit, stop_event)
