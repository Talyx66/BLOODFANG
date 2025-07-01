

import os
import requests

def load_payloads():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "payloads", "xss_payloads.txt"), "r") as f:
        return [p.strip() for p in f.readlines() if p.strip()]

def scan_xss(url, param, logger=print):
    payloads = load_payloads()
    logger(f"[XSS] Loaded {len(payloads)} payloads")
    for payload in payloads:
        full_url = f"{url}?{param}={payload}"
        try:
            r = requests.get(full_url, timeout=5)
            if payload in r.text:
                logger(f"[+] Possible XSS reflected: {payload}")
        except Exception as e:
            logger(f"[!] Error on payload {payload}: {e}")
