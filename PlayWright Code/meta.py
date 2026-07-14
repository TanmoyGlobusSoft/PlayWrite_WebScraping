from playwright.sync_api import sync_playwright
import random
import time

def human_sleep(a=0.8, b=2.0):
    time.sleep(random.uniform(a, b))

def human_type(locator, text):
    locator.click()
    human_sleep(0.5, 1)

    for ch in text:
        locator.type(ch, delay=random.randint(120, 250))
        time.sleep(random.uniform(0.05, 0.2))

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
        "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&q=puma&search_type=keyword_unordered&sort_data[mode]=total_impressions&sort_data[direction]=desc&source=nav-header",
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
    

    # page.get_by_text("All ads", exact=True).click()
    # human_sleep(2,3)

    # # -------- Search Box --------
    # search = page.get_by_placeholder("Search by keyword or advertiser")

    # human_type(search, "Puma")

    # human_sleep(1,2)

    # page.keyboard.press("Enter")

    # human_sleep(5,7)

















    
    #------AD sCRAPING------
    buttons = page.get_by_role("button", name="See ad details")

    for i in range(2):
        buttons.nth(i).scroll_into_view_if_needed()
        human_sleep(1, 2)

        buttons.nth(i).hover()
        human_sleep(0.5, 1)

        buttons.nth(i).click()

        # <-- yahan scrape karenge
        human_sleep(5, 8)
        
        locator = page.locator("span").filter(has_text="Library ID:")

        print(locator.count())
        # Close details
        page.keyboard.press("Escape")
        human_sleep(2, 3)

    input("Press Enter to close...")
    browser.close()