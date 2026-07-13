from playwright.sync_api import sync_playwright
import os
from datetime import datetime
# traceback is used to display errors in more detailed way
import traceback



PRODUCT_URL = (
    "https://www.amazon.in/"
    "Lenovo-IdeaPad-Next-Gen-Keyboard-83UR009QIN/dp/B0H3PV7418/"
)

OUTPUT_DIR = "output"

# Create output folder if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

FILES = {
    "ALL": os.path.join(OUTPUT_DIR, "all_requests.txt"),
    "GET": os.path.join(OUTPUT_DIR, "GET.txt"),
    "POST": os.path.join(OUTPUT_DIR, "POST.txt"),
    "PUT": os.path.join(OUTPUT_DIR, "PUT.txt"),
    "PATCH": os.path.join(OUTPUT_DIR, "PATCH.txt"),
    "DELETE": os.path.join(OUTPUT_DIR, "DELETE.txt"),
    "OTHER": os.path.join(OUTPUT_DIR, "OTHER.txt"),
}

# Clear previous run
for file in FILES.values():
    with open(file, "w", encoding="utf-8") as f:
        pass

request_counter = 0


def save_request(request):
    global request_counter

    request_counter += 1

    try:
        resource_type = request.resource_type
    except Exception:
        resource_type = "Unknown"

    try:
        frame_url = request.frame.url
    except Exception:
        frame_url = "Unknown"

    data = f"""
Request #{request_counter}
Method         : {request.method}
URL            : {request.url}
Resource Type  : {resource_type}
Frame URL      : {frame_url}
----------------------------------------------------------
"""

    # Save in ALL
    with open(FILES["ALL"], "a", encoding="utf-8") as f:
        f.write(data)

    # Save by Method
    method = request.method.upper()

    if method in FILES:
        with open(FILES[method], "a", encoding="utf-8") as f:
            f.write(data)
    else:
        with open(FILES["OTHER"], "a", encoding="utf-8") as f:
            f.write(data)

    print(f"[{method}] {request.url}")

try:

    # Starts the Playwright engine.
    # p is the main Playwright object that gives access to Chromium, Firefox, and WebKit.
    # When the with block ends, Playwright automatically shuts down.
    with sync_playwright() as p:
        # Launches a Chromium browser.
        # headless=False → Opens a visible browser window.
        # slow_mo=100 → Waits 100 ms after every Playwright action (useful for debugging).
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
        )

        # Creates a new Browser Context.
        # Think of a context as a fresh browser profile.
        # It has its own: Cookies, Local storage, Session storage and Cache
        context = browser.new_context()

        # Opens a new tab (page) inside the browser context.
        page = context.new_page()

        # It tells Playwright:
        # "Whenever this page sends any HTTP request, call the function save_request."
        # It does not call save_request immediately.
        # It registers an event listener.
        page.on("request", save_request)

        # visite to url...
        page.goto(
            # PRODUCT_URL → URL to visit.
            PRODUCT_URL,
            # wait_until="networkidle" → Wait until there are almost no network requests for a short period before considering the page loaded.
            wait_until="networkidle",
            # timeout=60000 → Wait up to 60 seconds before raising a timeout error.
            timeout=60000,
        )

        # wait for 10 seconds before close
        page.wait_for_timeout(10000)
        
        # Closes all tabs, browser context and browser process
        browser.close()

except Exception:
    print("✘✘✘ ERROR OCCURRED ✘✘✘")
    traceback.print_exc()

finally:
    print("✓✓✓ Finished ✓✓✓")