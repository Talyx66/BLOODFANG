
import requests
import random

def load_payloads(path="core/payloads/sql_payloads.txt"):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_random_user_agent():
    with open("data/user_agents.txt", "r") as f:
        return random.choice(f.read().splitlines())

def scan_sqli(target_url, param="id", logger=print):
    payloads = load_payloads()
    headers = {"User-Agent": get_random_user_agent()}
    logger(f"[>] Scanning {target_url} for SQL Injection on parameter '{param}'")

    for payload in payloads:
        test_url = f"{target_url}?{param}={payload}"
        try:
            r = requests.get(test_url, headers=headers, timeout=8)
            # Simple error-based detection example:
            errors = ["you have an error in your sql syntax", "warning: mysql", "unclosed quotation mark"]
            if any(e.lower() in r.text.lower() for e in errors):
                logger(f"[!!] Possible SQL Injection found with payload: {payload}")
        except Exception as e:
            logger(f"[X] Error with payload {payload}: {e}")
