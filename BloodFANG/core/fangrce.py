
import requests
import random

def load_payloads(path="core/payloads/xss_payloads.txt"):
    import os

def load_payloads():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "payloads", "xss_payloads.txt")
    with open(path, 'r') as f:
        return f.read().splitlines()

        return [line.strip() for line in f if line.strip()]

def get_random_user_agent():
    with open("data/user_agents.txt", "r") as f:
        return random.choice(f.read().splitlines())

def scan_xss(target_url, param="q", logger=print):
    payloads = load_payloads()
    headers = {"User-Agent": get_random_user_agent()}
    logger(f"[>] Scanning {target_url} for XSS on parameter '{param}'")

    for payload in payloads:
        test_url = f"{target_url}?{param}={payload}"
        try:
            r = requests.get(test_url, headers=headers, timeout=8)
            if payload in r.text:
                logger(f"[!!] XSS Found! Payload: {payload}")
        except Exception as e:
            logger(f"[X] Error with payload {payload}: {e}")
