import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def discover_api_endpoints(base_url, common_endpoints=None, logger=print):
    """
    Discover API endpoints by crawling common paths and scraping for endpoints.
    """
    if common_endpoints is None:
        common_endpoints = [
            "/api/", "/api/v1/", "/api/v2/", "/rest/", "/graphql", "/wp-json/"
        ]

    headers = {"User-Agent": "BloodFANG-API-Discovery"}

    logger(f"[>] Starting API endpoint discovery on {base_url}")

    for endpoint in common_endpoints:
        url = urljoin(base_url, endpoint)
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                logger(f"[!!] Found active endpoint: {url}")

                # Try to parse JSON or HTML for further links
                content_type = r.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    logger(f"    JSON response found at {url}")
                elif "html" in content_type:
                    soup = BeautifulSoup(r.text, "html.parser")
                    links = set(a['href'] for a in soup.find_all('a', href=True))
                    logger(f"    Found {len(links)} links on {url}")
            else:
                logger(f"[-] {url} returned status {r.status_code}")
        except Exception as e:
            logger(f"[X] Error accessing {url} - {e}")
