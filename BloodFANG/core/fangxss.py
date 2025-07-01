
import os

def load_payloads():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "payloads", "xss_payloads.txt")
    with open(path, 'r') as f:
        return f.read().splitlines()

def scan_xss(url, param, log_func=print):
    payloads = load_payloads()
    log_func(f"[+] Loaded {len(payloads)} payloads.")

    for payload in payloads:
        test_url = f"{url}?{param}={payload}"
        log_func(f"[*] Testing: {test_url}")
        # Add your XSS testing logic here (e.g., requests.get and response analysis)

def run():
    url = input("Target URL (e.g. http://test.com/page): ").strip()
    param = input("Parameter to test (e.g. search): ").strip()
    scan_xss(url, param)
