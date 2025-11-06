# BloodFANG/core/fangapi.py
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

ENDPOINTS = _load_payloads("api_endpoints.txt", ["/api/","/api/v1/","/v1/","/graphql"])

def discover_api_endpoints(base,emit,stop_event=None):
    emit(f"[API] Discovery on {base}")
    for ep in ENDPOINTS:
        if stop_event and stop_event.is_set(): emit("[API] Stopped."); return
        u = base.rstrip("/") + ep
        try:
            r = requests.get(u,timeout=6,verify=False)
            emit(f"[API] {r.status_code} {u}")
            if r.status_code==200: emit(f"[API] Found endpoint: {u}")
        except Exception as e: emit(f"[API] Error: {e}")
        time.sleep(0.25)
    emit("[API] Complete.")

def run(target,emit,stop_event=None):
    discover_api_endpoints(target,emit,stop_event)
