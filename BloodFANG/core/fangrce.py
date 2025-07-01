import requests
import random

def load_payloads(path="core/payloads/rce_payloads.txt"):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_random_user_agent():
    with open("data/user_agents.txt", "r") as f:
        return random.choice(f.read().splitlines())

def scan_rce(target_url, param="cmd", logger=print):
    payloads = load_payloads()
    headers = {"User-Agent": get_random_user_agent()}
    logger(f"[>] Scanning {target_url} for RCE on parameter '{param}'")

    for payload in payloads:
        test_url = f"{target_url}?{param}={payload}"
        try:
            r = requests.get(test_url, headers=headers, timeout=8)
            # Check for expected command output, e.g., typical shell command output
            if "uid=" in r.text or "root" in r.text or "command not found" not in r.text:
                logger(f"[!!] Possible RCE found with payload: {payload}")
        except Exception as e:
            logger(f"[X] Error with payload {payload}: {e}")
