# fangxss.py
"""
Basic XSS scanner entrypoints:
 - scan_xss(url, param, emit, stop_event=None)
 - scan(target, emit, stop_event=None)  # target = "URL::param"
"""
import requests
import urllib.parse
import time
import warnings
import os
from pathlib import Path

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

def _find_payload_dir():
    here = Path(__file__).resolve().parent
    cand = here / "payloads"
    if cand.exists():
        return cand
    cur = here
    for _ in range(6):
        p = cur / "payloads"
        if p.exists():
            return p
        p2 = cur / "BloodFANG" / "core" / "payloads"
        if p2.exists():
            return p2
        cur = cur.parent
    env = os.getenv("BLOODFANG_PAYLOADS")
    if env:
        p = Path(env)
        if p.exists():
            return p
    return cand

PAYLOAD_DIR = _find_payload_dir()

def _load_payloads(name, fallback):
    try:
        f = PAYLOAD_DIR / name
        if f.exists():
            text = f.read_text(encoding="utf-8", errors="ignore")
            lines = [L.strip() for L in text.splitlines() if L.strip() and not L.strip().startswith("#")]
            if lines:
                return lines
    except Exception:
        pass
    return fallback

PAYLOADS = _load_payloads("xss_payloads.txt", [
    "<script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "<svg/onload=alert(1)>",
])

def _compose(url, param, payload):
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q = [(k, v) for (k, v) in q if k != param]
    q.append((param, payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q, doseq=True)))

def scan_xss(url, param, emit, stop_event=None):
    if not url:
        emit("[XSS] Missing URL.")
        return
    if not param:
        emit("[XSS] Missing parameter.")
        return

    emit(f"[XSS] Target: {url} param={param}")
    for payload in PAYLOADS:
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            emit("[XSS] Stopped by user.")
            return
        t = _compose(url, param, payload)
        try:
            r = requests.get(t, timeout=8, verify=False)
            emit(f"[XSS] {r.status_code} → {t}")
            if payload in r.text:
                emit(f"[XSS] Reflection found for payload: {payload}")
        except requests.exceptions.RequestException as re:
            emit(f"[XSS] Request error: {re}")
        except Exception as e:
            emit(f"[XSS] Unexpected error: {e}")
        time.sleep(0.25)
    emit("[XSS] Scan complete.")

def scan(target, emit, stop_event=None):
    url, param = (target.split("::", 1) + [""])[:2]
    scan_xss(url, param, emit, stop_event)