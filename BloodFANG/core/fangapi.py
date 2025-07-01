import requests

def discover_api_endpoints(base_url, logger=print):
    common_endpoints = ["api", "v1", "admin", "auth", "user", "login", "logout", "config"]
    logger(f"[API] Starting enumeration on {base_url}")
    for ep in common_endpoints:
        full_url = f"{base_url.rstrip('/')}/{ep}"
        try:
            r = requests.get(full_url, timeout=5)
            if r.status_code < 400:
                logger(f"[+] Found endpoint: {full_url} [{r.status_code}]")
        except Exception as e:
            logger(f"[!] Error probing {full_url} -> {e}")
