url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=political_and_issue_ads&country=IN&is_targeted_country=false&media_type=all&sort_data[mode]=total_impressions&sort_data[direction]=desc"


from pathlib import Path
from playwright.sync_api import sync_playwright, Error
import time
import random

# Configuration
PROJECT_ROOT = Path(__file__).parent
BROWSER_PROFILE = PROJECT_ROOT/"browser_profile"

# Browser Manager
class Browser_Manager:
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
    
    def start(self):
        # This line manually starts the Playwright engine and returns a Playwright object that you can use to launch browsers.
        self.playwright = sync_playwright().start()

    def launch_browser(self):
        # launches a Chromium browser with a persistent user profile and stores the browser context in self.context
        # persistent browser this browser remembers Cookies, Login sessions, Local Storage, Session Storage, Browser preferences and Cache
        self.context = self.playwright.chromium.launch_persistent_context(
            # Specifies where the browser profile will be stored.
            user_data_dir=str(BROWSER_PROFILE),
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            timezone_id="Asia/Kolkata",
            headless=False,
            args=["--start-maximized"]
        )
    
    def get_page(self):
        if self.context.pages:
            # Return an existing page
            self.page = self.context.pages[0]
        else:
            # create a new one
            self.page = self.context.new_page()
        
        return self.page
    
    def close(self):
        if self.context:
            self.context.close()
        
        if self.playwright:
            self.playwright.stop()

def wait_for_close(page):
    while True:
        try:
            # If the page is closed manually, this will raise an exception
            page.title()
            time.sleep(1)

        except Error:
            print("Browser was closed by the user.")
            break


def human_sleep(a=0.8, b=2.0):
    time.sleep(random.uniform(a, b))

def human_type(locator, text):
    locator.click()
    human_sleep(0.5, 1)

    for ch in text:
        locator.type(ch, delay=random.randint(120, 250))
        time.sleep(random.uniform(0.05, 0.2))

def human_click(locator):
    locator.scroll_into_view_if_needed()
    locator.hover()
    human_sleep(0.2,0.5)
    locator.click()

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

def get_ads_data(ads):
    pass

if __name__ == "__main__":
    browser = Browser_Manager()
    browser.start()
    browser.launch_browser()
    page = browser.get_page()

    # page.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=political_and_issue_ads&country=IN&is_targeted_country=false&media_type=all&sort_data[mode]=total_impressions&sort_data[direction]=desc", wait_until="networkidle")    
    page.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&q=football%20ads&search_type=keyword_unordered&sort_data[direction]=desc&sort_data[mode]=total_impressions", wait_until="networkidle")    
    
    # # Search Country -> India
    # select_country("India")

    # # Open and Select Ad Category
    # human_click(page.get_by_text('Ad category', exact=True))
    # human_click(page.get_by_text("All ads", exact=True))

    # # Search advertiser / keyword
    # search_box = page.get_by_placeholder("Search by keyword or advertiser")
    # search_box.fill("")
    # human_type(search_box, "football ads")
    # human_sleep(0.5, 1)
    # page.keyboard.press("Enter")
    # page.wait_for_load_state("networkidle")
    # human_sleep(2, 4)  
    
    # print("Search Done!")

    # Wait until ads are loaded
    page.get_by_role("button", name="See ad details").first.wait_for()

    # All "See ad details" buttons
    buttons = page.get_by_role("button", name="See ad details")

    print(f"Ads Found: {buttons.count()}")

    for i in range(buttons.count()):

        # Go from button -> parent ad card
        card = buttons.nth(i).locator(
            "xpath=ancestor::div[contains(@class,'xh8yej3')][1]"
        )

        advertiser_name = None
        library_id = None
        start_date = None
        ad_status = None
        ad_description = None
        image_url = None
        video_url = None
        destination_url = None
        call_to_action = None

        # Extract Data
        try:
            advertiser_name = card.locator("a[href*='facebook.com']").first.inner_text()
        except:
            pass

        try:
            library_id = card.locator("text=/Library ID:/").inner_text()
        except:
            pass

        try:
            start_date = card.locator("text=/Started running/").inner_text()
        except:
            pass

        try:
            ad_status = card.locator("text=Active").inner_text()
        except:
            pass

        try:
            ad_description = card.locator("div[style*='white-space: pre-wrap']").first.inner_text()
        except:
            pass

        try:
            video_url = card.locator("video").get_attribute("src")
        except:
            pass

        try:
            destination_url = card.locator("a[href]").last.get_attribute("href")
        except:
            pass

        try:
            call_to_action = card.get_by_role("button").last.inner_text()
        except:
            pass

        # print("=" * 80)
        # print("Advertiser      :", advertiser_name)
        # print("Library ID      :", library_id)
        # print("Status          :", ad_status)
        # print("Start Date      :", start_date)
        # print("Description     :", ad_description)
        # print("Video URL       :", video_url)
        # print("Destination URL :", destination_url)
        # print("CTA             :", call_to_action)


    wait_for_close(page)

    browser.close()

