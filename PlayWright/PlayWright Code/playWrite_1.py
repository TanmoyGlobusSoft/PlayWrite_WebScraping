# Imports the sync_playwright function from Playwright's synchronous API so you can automate browsers using normal Python code.
from playwright.sync_api import sync_playwright

# expect() is part of Playwright's assertion library. It is primarily used in Playwright's testing framework to verify that the page is in the expected state
from playwright.sync_api import expect

from bs4 import BeautifulSoup

def get_details(n):
    details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').nth(n).inner_html()
    soup = BeautifulSoup(details, "html.parser")
    all_tr = soup.find_all("tr")
    Details_dict = {}
    for tr in all_tr:
        th = tr.find("th")
        td = tr.find("td")
        Details_dict[th.get_text(strip=True)] = td.get_text(strip=True)
    return Details_dict

# Starts the Playwright engine.
# with is a context manager that automatically starts Playwright at the beginning and closes it when the block ends.
# p is the Playwright object that gives access to browsers like Chromium, Firefox, and WebKit.
with sync_playwright() as p:
    # Launches a new Chromium browser instance.
    # The browser starts in headless mode (without a visible window) by default.
    # The browser object is stored in the variable browser for further actions like opening pages and navigating to websites.
    # browser = p.chromium.launch(headless=False, slow_mo=500)
    browser = p.chromium.launch()

    page = browser.new_page()

    page.goto(
        "https://www.amazon.in/ASUS-Upgradeable-Keyboard-Graphite-FA506NCG-HN199W/dp/B0FM3C4L2F/ref=sr_1_6?sr=8-6",
    )

    # ### Phase 1 — Playwright Basics
    # # page.get_by_role(role, name="...")
    # # role → What kind of element it is (button, link, textbox, checkbox, etc.)
    # # name → The visible text or accessible name of that element.
    # page.locator("#buy-now-button").click()

    # page.locator('input[name="email"]').fill("user@amazon.in")



    # ### Phase 2 — Locators
    # ## CSS Selectors
    # # Locate by ID
    # title = page.locator("span#productTitle").text_content()
    # # print(title)

    # # Locate by Class
    # emi = page.locator(".a-hidden").all_text_contents()
    # # print(emi)

    # # Locate by Tag
    # article = page.locator("article").all_text_contents()
    # # print(article)

    # # Locate by Attribute
    # budget = page.locator('[aria-hidden="true"]').all_text_contents()
    # # print(budget)

    # ## XPath
    # # quantity = page.locator('//span[@id="a-autoid-0-announce"]').all_text_contents()
    # sold_by = page.locator('//a[@href="/gp/help/seller/at-a-glance.html/ref=dp_merchant_link?ie=UTF8&seller=AJ6SIZC8YQDZX&asin=B0FM3C4L2F&ref_=dp_merchant_link&isAmazonFulfilled=1"]').all_text_contents()
    # # print(quantity)

    # ## Text Locator
    # payment = page.get_by_text('Secure transaction').all_text_contents()
    # # print(payment)

    # ## Role Locator
    # care = page.get_by_role("span", name="1").all_text_contents()
    # # print(care)

    # # Placeholder Locator
    # price = page.locator('input[placeholder="Enter URL where you found the price lower"]').all_text_contents()
    # # print(price)

    # # Label Locator
    # div = page.get_by_label("div").all_text_contents()
    # # print(div)



    # ### Phase 3 — Browser Automation
    # # goto()
    # page.goto("https://www.amazon.in/EUPHORIA-Rolls-Royce-Phantom-Diecast/dp/B0DBG89NR7/ref=sr_1_3_sspa?sr=8-3-spons&aref=9D5szasF8g&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1")

    # # fill()
    # page.locator("#twotabsearchtextbox").fill("poco m2 pro")

    # # click()
    # # page.locator("#nav-search-submit-button").click()

    # # press()
    # page.locator("#twotabsearchtextbox").press("Enter")

    # # wait_for_selector()
    # page.wait_for_selector(".a-dropdown-label")

    # # wait_for_load_state()
    # page.wait_for_load_state("load")

    # # expect()
    # expect(page).to_have_title("Amazon.in : poco m2 pro")
    # expect(page.locator("#a-autoid-1-announce")).to_be_visible()



    # ### Phase 4 — Data Extraction
    # Product_Name = page.locator("#productTitle").nth(0).text_content().strip()
    # # print(Product_Name)

    # Brand = page.locator('tr:has-text("Brand") td').nth(1).inner_text()
    # # print(Brand)

    # Price = page.locator("span.a-price-whole").nth(1).inner_text()
    # # print(Price)

    # Rating = (
    #     page.locator('span.a-icon-alt:has-text("out of 5 stars")').nth(1).inner_text()
    # )
    # # print(Rating)

    # # Reviews
    # Reviews = page.locator("span#acrCustomerReviewText").nth(0).inner_text()
    # # print(Reviews)

    # # Image URL's
    # Images = page.locator("span.a-button-text[id^='a-autoid-'] img")
    # Image_URLs = ""
    # for img in range(Images.count()):
    #     Image_URLs += ", " + Images.nth(img).get_attribute("src")
    # # print(Image_URLs)

    # # Product ASIN
    # Product_ASIN = page.url
    # Product_ASIN = Product_ASIN.split("/")[-2]
    # # print(Product_ASIN)

    # # Product Details
    # product_details = page.locator(
    #     "table.a-normal.a-spacing-micro[role='list'] tbody"
    # ).inner_html()
    # soup = BeautifulSoup(product_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # details = {}
    # for tr in all_tr:
    #     td = tr.find_all("td")
    #     # print(td[0].get_text(strip=True), " >><< ", td[1].get_text(strip=True))
    #     details[td[0].get_text(strip=True)] = td[1].get_text(strip=True)
    # # print(details)
    
    # # Brand Details
    # Brand_Details = page.locator("div.a-section.a-spacing-base.brand-snapshot-flex-row[role='listitem']").all_text_contents()
    # Brand_Details = ", ".join(Brand_Details)
    # # print(brand_details)
    
    # # Additional Details 
    # Additional_Details = get_details(0)
    # print(Additional_Details)
    
    # # Display Details
    # Display_Details = get_details(1)
    # print(Display_Details)
    
    # # Connectivity Details
    # Connectivity_Details = get_details(2)
    # print(Connectivity_Details)      
    
    # # Ports & Slots Details
    # Ports_Slots_Details = get_details(3)
    # print(Ports_Slots_Details)
    
    # # Audio Details
    # Audio_Details = get_details(4)
    # print(Audio_Details)
    
    # # Processor Details
    # Processor_Details = get_details(5)
    # print(Processor_Details)
    
    # # Item details
    # Item_details = get_details(6)
    # print(Item_details)
    
    # # Memory Details
    # Memory_Details = get_details(7)
    # print(Memory_Details)
    
    # # Battery Details
    # Battery_Details = get_details(8)
    # print(Battery_Details)
    
    # Input_Details
    Input_Details = get_details(9)
    print(Input_Details)

    ### Phase 5 — Pagination














    # page.wait_for_timeout(3000)
    browser.close()
