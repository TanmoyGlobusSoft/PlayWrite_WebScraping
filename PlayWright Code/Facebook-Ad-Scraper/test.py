"""
automate.py

Loads the "GraphQL & JSON Network Extractor" Chrome extension (unpacked),
searches Facebook Ad Library for a keyword ("puma" by default) with some
humanlike mouse/typing/scroll behavior, then drives the extension's popup UI
to Extract and Download whatever GraphQL/JSON responses were captured.

Facebook Ad Library is a good target for this: its search results are loaded
almost entirely via GraphQL calls to facebook.com/api/graphql/, so this
should capture plenty of real GraphQL payloads (ad content, targeting info,
pagination cursors, etc).

Notes:
- Extensions require a real (non-headless) Chromium window.
- Facebook's DOM/selectors change often and it may show login walls,
  cookie/consent dialogs, or bot-detection challenges depending on region,
  cookies, and luck. Selectors below use resilient text/role/placeholder
  matching with try/except fallbacks, but you may still need to tweak them.
"""

import asyncio
import random
import re
import sys
from pathlib import Path
import requests

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_DIR = Path(__file__).parent
EXTENSION_PATH = BASE_DIR / "extension"
USER_DATA_DIR = BASE_DIR / ".chrome-profile"
DOWNLOAD_DIR = BASE_DIR / "downloads"

DEFAULT_SEARCH_TERM = "puma"
COUNTRY = "India"
AD_LIBRARY_URL = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&q=bengaluru&search_type=keyword_unordered&sort_data[direction]=desc&sort_data[mode]=total_impressions"

# async def → Defines an asynchronous function that must be called with await.

async def human_pause(a: float = 0.25, b: float = 0.7):
    # await asyncio.sleep(...) → Asynchronously waits for that duration without blocking other async tasks.
    await asyncio.sleep(random.uniform(a, b))


async def human_mouse_wander(page, moves: int = 3):
    """Move the mouse to a few semi-random points, like someone glancing
    around the page before doing anything."""
    for _ in range(moves):
        x = random.randint(150, 900)
        y = random.randint(120, 600)
        await page.mouse.move(x, y, steps=random.randint(8, 20))
        await human_pause(0.1, 0.35)


async def human_type(locator, text: str):
    """Click into a field and type character-by-character with irregular
    delays, occasionally pausing briefly like someone thinking."""
    await locator.click()
    await human_pause()
    for ch in text:
        await locator.type(ch, delay=random.uniform(70, 190))
        if random.random() < 0.12:
            await human_pause(0.15, 0.45)


async def human_scroll(page, total_amount: int = 900, steps: int = 8):
    for _ in range(steps):
        await page.mouse.wheel(0, total_amount / steps)
        await human_pause(0.15, 0.4)

async def select_country(page):
    """Select country in Facebook Ad Library."""

    try:
        # Open country selector
        await page.get_by_text("India", exact=True).nth(0).click()

        await human_pause(1, 2)

        # Search for country
        search = page.locator("input[placeholder='Search for country']")
        await search.fill("")
        await human_type(search, COUNTRY)

        await human_pause(1.5, 2.5)

        # Select the country from the results
        await page.get_by_text(COUNTRY, exact=True).click()

        print(f"Selected country: {COUNTRY}")

    except Exception as e:
        print(f"Could not interact with the country selector: {e}")


async def Selects_Advertising_Category(page):
    await page.get_by_text("Ad category", exact=True).nth(0).click()
    await human_pause(0.5, 1.0)

    await page.get_by_text("All ads", exact=True).click()
    await human_pause(0.5, 1.0)



async def type_keyword(page, search_term):
    PLACEHOLDERS = [
        "Choose an ad category",
        "Search by keyword or advertiser",
        "Search by keyword",
        "Search",
    ]
    
    search_box = None

    for placeholder in PLACEHOLDERS:
        try:
            locator = page.get_by_placeholder(
                re.compile(placeholder, re.I)
            )

            await locator.wait_for(state="visible", timeout=2000)

            print(f'✓ Found search box with placeholder: "{placeholder}"')
            search_box = locator
            break

        except PlaywrightTimeoutError:
            continue

    if search_box is None:
        raise Exception("Could not find the search box using any known placeholder.")

    await human_type(search_box, search_term)
    await human_pause(0.4, 0.9)
    await page.keyboard.press("Enter")

async def scrape_ad(dialog):

    text = await dialog.inner_text()

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    m = re.search(r"Library ID:\s*(\d+)", text)
    library_id = m.group(1) if m else ""

    status = ""
    if "Active" in lines:
        status = "Active"
    elif "Inactive" in lines:
        status = "Inactive"

    m = re.search(r"Started running on\s*(.*)", text)
    started_date = m.group(1).strip() if m else ""

    advertiser = ""

    for i, line in enumerate(lines):
        if line == "Sponsored" and i > 0:
            advertiser = lines[i - 1]
            break

    domain = ""

    for line in lines:
        if "." in line and line == line.upper():
            domain = line
            break

    # cta = ""

    # for word in [
    #     "Shop Now",
    #     "Learn More",
    #     "Book Now",
    #     "Sign Up",
    #     "Download",
    #     "Apply Now",
    #     "Contact Us"
    # ]:
    #     if word in text:
    #         cta = word
    #         break

    return {
        "Library ID": library_id,
        "Status": status,
        "Started Date": started_date,
        "Brand": advertiser,
        "Landing Domain": domain,
        
    }


# icons
async def get_platforms(dialog):

    platform_div = dialog.locator("text=Platforms").locator("..")
    icons = platform_div.locator("div[style*='mask-position']")

    platform_map = {
        ("uhBloS7nYQk.webp", "0px -955px"): "Facebook",
        ("uhBloS7nYQk.webp", "0px -1007px"): "Instagram",

        ("TL8NfUewwsW.webp", "-388px -732px"): "Messenger",
        ("TL8NfUewwsW.webp", "-387px -766px"): "Audience Network",
    }

    platforms = []

    for j in range(await icons.count()):

        style = await icons.nth(j).get_attribute("style") or ""

        for (sprite, pos), name in platform_map.items():

            if sprite in style and pos in style:
                platforms.append(name)
                break

    return platforms



async def main():
    search_term = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SEARCH_TERM
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    if not EXTENSION_PATH.exists():
        print(f"Extension folder not found at {EXTENSION_PATH}")
        sys.exit(1)

    async with async_playwright() as p:
        print("Launching Chromium with the extension loaded...")
        context = await p.chromium.launch_persistent_context(
            str(USER_DATA_DIR),
            headless=False,  # extensions require a real, non-headless window
            accept_downloads=True,
            args=[
                f"--disable-extensions-except={EXTENSION_PATH}",
                f"--load-extension={EXTENSION_PATH}",
                "--no-first-run",
            ],
        )

        # --- Grab the extension's background service worker to read its id ---
        background = context.service_workers[0] if context.service_workers else None
        if background is None:
            background = await context.wait_for_event("serviceworker", timeout=5000)
        extension_id = background.url.split("/")[2]
        print("Extension loaded, id:", extension_id)

        page = await context.new_page()

        await page.goto(
            AD_LIBRARY_URL,
            wait_until="domcontentloaded"
        )


        #------AD sCRAPING------
        buttons = page.get_by_role("button", name="See ad details")

        buttons_count = await buttons.count()
        print(f"Number of ads: {buttons_count}")

        for ad_index in range(3):

            await buttons.nth(ad_index).scroll_into_view_if_needed()
            await human_pause(1, 2)

            await buttons.nth(ad_index).hover()
            await human_pause(0.5, 1)

            await buttons.nth(ad_index).click()

            # Popup load hone do
            await human_pause(3, 5)

            # Popup
            dialog = page.locator("div[role='dialog']").nth(1)

            # Data scrape
            data = await scrape_ad(dialog)

        # get data from Transparency option 

            transparency = {
                "Available": False,
                "Regions": {}
            }

            if await dialog.get_by_text("Transparency by location").count() > 0:

                transparency["Available"] = True

                # Open section
                section = dialog.get_by_text("Transparency by location")
                await section.scroll_into_view_if_needed()
                await human_pause(1, 2)

                await section.click()
                await human_pause(2, 3)

                # Tabs
                tabs = dialog.locator("div[role='tab']")

                print("Total Tabs:", await tabs.count())

                for t in range(await tabs.count()):

                    # Fresh locator every iteration
                    tab = dialog.locator("div[role='tab']").nth(t)

                    region = await tab.get_attribute("aria-label")
                    if not region:
                        region = (await tab.inner_text()).strip()

                    print(f"\nOpening : {region}")

                    await tab.scroll_into_view_if_needed()
                    await human_pause(0.5, 1)

                    await tab.click()

                    await human_pause(2, 3)

                    region_data = {
                        "Reach": "",
                        "Audience": []
                    }

                    # Reach
                

                    # Fresh rows
                    rows = dialog.locator("table tbody tr")
                    await rows.first.wait_for(state="visible", timeout=10000)
                    print(region, "Rows:", await rows.count())

                    total_reach = 0

                

                    for r in range(await rows.count()):

                        cols = rows.nth(r).locator("td")

                        if await cols.count() >= 4:

                            row_reach = await cols.nth(3).inner_text().strip()

                            try:
                                total_reach += int(row_reach)
                            except:
                                pass

                            region_data["Audience"].append({
                                "Location": cols.nth(0).inner_text().strip(),
                                "Age": cols.nth(1).inner_text().strip(),
                                "Gender": cols.nth(2).inner_text().strip(),
                                "Reach": row_reach
                            })

                    region_data["Reach"] = total_reach

                    transparency["Regions"][region] = region_data
            # ------------------------------------------------------

        
            platforms = await get_platforms(dialog)

            data["Platforms"] = platforms

            data["Transparency"] = transparency

            
            # Determine the Ad Library tab's real chrome tab id
            # Must happen before opening the popup page, since opening a new tab
            # changes which tab chrome considers "active".
            tab_id = await background.evaluate(
                """async () => {
                    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
                    return tabs[0] && tabs[0].id;
                }"""
            )
            if not tab_id:
                raise RuntimeError("Could not determine the Ad Library tab's id from the extension.")
            print("Ad Library tab id:", tab_id)

            # --- Open the extension popup directly, targeting that tab ---
            popup = await context.new_page()
            await popup.goto(f"chrome-extension://{extension_id}/popup.html?tabId={tab_id}")

            print('Clicking "Extract"...')
            await popup.click("#extractBtn")
            await popup.wait_for_timeout(1200)

            count_text = await popup.locator("#count").inner_text()
            print(f"Extension reports {count_text} captured response(s).")
            if count_text == "0":
                print(
                    "No JSON/GraphQL responses were captured. Facebook may have shown a "
                    "login wall or the results didn't finish loading — try re-running, "
                    "or increase the wait/scroll time above."
                )

            print('Clicking "Download"...')
            async with popup.expect_download() as download_info:
                await popup.click("#downloadBtn")
            download = await download_info.value

            save_path = DOWNLOAD_DIR / download.suggested_filename
            await download.save_as(str(save_path))
            print("Saved captured data to:", save_path)

            # Close the extension popup tab
            await popup.close()

            # Return to the Facebook tab (optional but recommended)
            await page.bring_to_front()

            await page.keyboard.press("Escape")

            await human_pause(2, 3)
        

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
