from playwright.sync_api import sync_playwright
import random
import time
import re

from db import save_to_db      
def human_sleep(a=0.8, b=2.0):
    time.sleep(random.uniform(a, b))

def human_type(locator, text):
    locator.click()
    human_sleep(0.5, 1)

    for ch in text:
        locator.type(ch, delay=random.randint(120, 250))
        time.sleep(random.uniform(0.05, 0.2))
# values
def scrape_ad(dialog):

    text = dialog.inner_text()

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
def get_platforms(dialog):

    platform_div = dialog.locator("text=Platforms").locator("..")
    icons = platform_div.locator("div[style*='mask-position']")

    platform_map = {
        ("uhBloS7nYQk.webp", "0px -955px"): "Facebook",
        ("uhBloS7nYQk.webp", "0px -1007px"): "Instagram",

        ("TL8NfUewwsW.webp", "-388px -732px"): "Messenger",
        ("TL8NfUewwsW.webp", "-387px -766px"): "Audience Network",
    }

    platforms = []

    for j in range(icons.count()):

        style = icons.nth(j).get_attribute("style") or ""

        for (sprite, pos), name in platform_map.items():

            if sprite in style and pos in style:
                platforms.append(name)
                break

    return platforms

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        slow_mo=80
    )

    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="Asia/Kolkata"
    )

    page = context.new_page()

    page.goto(
        "https://www.facebook.com/ads/library/",
        wait_until="networkidle"
    )

    human_sleep(3,5)

    # Mouse movement
    page.mouse.move(250, 180, steps=40)
    human_sleep()

    # -------- Ad Category --------
    # comboboxes = page.locator("div[role='combobox']")

    # print("Total:", comboboxes.count())

    # for i in range(comboboxes.count()):
    #     print(i, comboboxes.nth(i).inner_text())
    # -------- country Category --------

    def select_country(country_name):
    # Country dropdown
        country = page.locator("div[role='combobox']").nth(0)
        country.click()
        human_sleep(1, 2)

        # Search
        search = page.locator("input[placeholder='Search for country']")
        search.fill("")
        human_type(search, country_name)
        human_sleep(1.5, 2.5)

        # Country row
        rows = page.locator("div[role='gridcell']")

        for i in range(rows.count()):
            row = rows.nth(i)

            if row.inner_text().strip() == country_name:
                row.click()
                human_sleep(1, 2)
                return

        print(f"{country_name} not found")
    select_country("United States")
    # -------- Ad Category --------

    ad_category = page.locator("div[role='combobox']").nth(1)

    ad_category.scroll_into_view_if_needed()
    human_sleep(1, 2)

    ad_category.hover()
    human_sleep(0.5, 1)

    ad_category.click()

    human_sleep(2, 3)
    

    page.get_by_text("All ads", exact=True).click()
    human_sleep(2,3)

    # -------- Search Box --------
    search = page.get_by_placeholder("Search by keyword or advertiser")

    human_type(search, "Puma")

    human_sleep(1,2)

    page.keyboard.press("Enter")

    human_sleep(5,7)
    
    #------AD sCRAPING------
    buttons = page.get_by_role("button", name="See ad details")

    for ad_index in range(12):

        buttons.nth(ad_index).scroll_into_view_if_needed()
        human_sleep(1, 2)

        buttons.nth(ad_index).hover()
        human_sleep(0.5, 1)

        buttons.nth(ad_index).click()

        # Popup load hone do
        human_sleep(3, 5)

        # Popup
        dialog = page.locator("div[role='dialog']").nth(1)

        # Data scrape
        data = scrape_ad(dialog)

        # -------------------------------optional
 # -------------------- Transparency --------------------

       # -------------------- Transparency --------------------

        transparency = {
            "Available": False,
            "Regions": {}
        }

        if dialog.get_by_text("Transparency by location").count() > 0:

            transparency["Available"] = True

            # Open section
            section = dialog.get_by_text("Transparency by location")
            section.scroll_into_view_if_needed()
            human_sleep(1, 2)

            section.click()
            human_sleep(2, 3)

            # Tabs
            tabs = dialog.locator("div[role='tab']")

            print("Total Tabs:", tabs.count())

            for t in range(tabs.count()):

                # Fresh locator every iteration
                tab = dialog.locator("div[role='tab']").nth(t)

                region = tab.get_attribute("aria-label") or tab.inner_text().strip()

                print(f"\nOpening : {region}")

                tab.scroll_into_view_if_needed()
                human_sleep(0.5, 1)

                tab.click()

                human_sleep(2, 3)

                region_data = {
                    "Reach": "",
                    "Audience": []
                }

                # Reach
               

                # Fresh rows
                rows = dialog.locator("table tbody tr")
                rows.first.wait_for(state="visible", timeout=10000)
                print(region, "Rows:", rows.count())

                total_reach = 0

              

                for r in range(rows.count()):

                    cols = rows.nth(r).locator("td")

                    if cols.count() >= 4:

                        row_reach = cols.nth(3).inner_text().strip()

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

       
        platforms = get_platforms(dialog)

        data["Platforms"] = platforms

        data["Transparency"] = transparency

        
        save_to_db(data)
        # Popup band
        page.keyboard.press("Escape")

        human_sleep(2, 3)
    input("Press Enter to close...")
    browser.close()