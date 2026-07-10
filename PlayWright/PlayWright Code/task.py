import requests
from playwright.sync_api import sync_playwright

URL = "https://www.amazon.in/dp/B0CV427854"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context(viewport=None)
    page = context.new_page()

    api_calls = []

    page.on(
        "request",
        lambda req: api_calls.append((req.method, req.url))
        if req.resource_type in ("JS", "fetch")
        else None,
    )

    page.goto(URL, wait_until="domcontentloaded", timeout=120000)

    # Allow async API calls to complete
    page.wait_for_timeout(10000)

    print(f"\nFound {len(api_calls)} API calls\n")

    for method, url in sorted(set(api_calls)):
        # print(method, url)
        if method == "GET":
            res = requests.get(url=url)
            print(res.status_code)
            print(res.text)


    browser.close()


















