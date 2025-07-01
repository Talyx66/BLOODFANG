
import os
import requests

def load_payloads():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "payloads", "rce_payloads.txt"), "r") as f:
        return [p.strip() for p in f.readlines() if p.strip()]

def scan_rce(url, param, logger=print):
    payloads = load_payloads()
    logger(f"[RCE] Loaded {len(payloads)} payloads")
    for payload in payloads:
        full_url = f"{url}?{param}={payload}"
        try:
            r = requests.get(full_url, timeout=5)
            if "uid=" in r.text or "root" in r.text:
                logger(f"[+] RCE success: {payload}")
        except Exception as e:
            logger(f"[!] Error: {e}")
