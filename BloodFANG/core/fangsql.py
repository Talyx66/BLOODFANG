import os
import requests

def load_payloads():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "payloads", "sqli_payloads.txt"), "r") as f:
        return [p.strip() for p in f.readlines() if p.strip()]

def scan_sqli(url, param, logger=print):
    payloads = load_payloads()
    logger(f"[SQLi] Loaded {len(payloads)} payloads")
    for payload in payloads:
        test_url = f"{url}?{param}={payload}"
        try:
            r = requests.get(test_url, timeout=5)
            if any(err in r.text.lower() for err in ["sql", "syntax", "mysql", "error"]):
                logger(f"[+] SQLi detected with payload: {payload}")
        except Exception as e:
            logger(f"[!] Error: {e}")
