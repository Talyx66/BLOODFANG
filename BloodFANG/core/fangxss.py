# BloodFANG/core/fangxss.py
"""
Cross-Site Scripting scanner for BLOODFANG.
Detects reflected payloads via GET parameters.
"""
import requests, urllib.parse, time

PAYLOADS = [
    "<script>alert(1)</script>",
    "\"><img src=x onerror=alert(1)>",
    "'><svg/onload=alert(1)>",
    "<iframe src='javascript:alert(1)'></iframe>"
]

def _compose(url, param, payload):
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    q.append((param, payload))
    new_query = urllib.parse.urlencode(q, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def scan_xss(url, param, emit, stop_event=None):
    if not param:
        emit("[XSS] Missing parameter.")
        return
    emit(f"[XSS] Target: {url} param={param}")
    for p in PAYLOADS:
        if stop_event and stop_event.is_set():
            emit("[XSS] Stopped by user.")
            return
        target = _compose(url, param, p)
        try:
            r = requests.get(target, timeout=8, verify=False)
            emit(f"[XSS] {r.status_code} → {target}")
            if p in r.text:
                emit(f"[XSS] Reflection found for payload: {p}")
        except Exception as e:
            emit(f"[XSS] Request error: {e}")
        time.sleep(0.25)
    emit("[XSS] Scan complete.")

def scan(target, emit, stop_event=None):
    url, param = (target.split("::",1)+[""])[:2]
    scan_xss(url, param, emit, stop_event)
