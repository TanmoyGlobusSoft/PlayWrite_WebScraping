# Imports the sync_playwright function from Playwright's synchronous API so you can automate browsers using normal Python code.
from playwright.sync_api import sync_playwright

# expect() is part of Playwright's assertion library. It is primarily used in Playwright's testing framework to verify that the page is in the expected state
from playwright.sync_api import expect

from bs4 import BeautifulSoup

# Starts the Playwright engine.
# with is a context manager that automatically starts Playwright at the beginning and closes it when the block ends.
# p is the Playwright object that gives access to browsers like Chromium, Firefox, and WebKit.
with sync_playwright() as p:
    # Launches a new Chromium browser instance.
    # The browser starts in headless mode (without a visible window) by default.
    # The browser object is stored in the variable browser for further actions like opening pages and navigating to websites.
    browser = p.chromium.launch(headless=False, slow_mo=500)
    # browser = p.chromium.launch()

    page = browser.new_page()

    page.goto(
        "https://www.amazon.in/ASUS-Upgradeable-Keyboard-Graphite-FA506NCG-HN199W/dp/B0FM3C4L2F/ref=sr_1_6?sr=8-6"
    )

    # ### Phase 1
    # # page.get_by_role(role, name="...")
    # # role → What kind of element it is (button, link, textbox, checkbox, etc.)
    # # name → The visible text or accessible name of that element.
    # page.locator("#buy-now-button").click()

    # page.locator('input[name="email"]').fill("user@amazon.in")



    # ### Phase 2
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



    # ### Phase 3
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
    
    # # Additional details 
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Additional details ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Additional_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Additional_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # # print(Additional_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Additional details ")').click()
    
    # # Display 
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Display ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Display_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Display_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Display_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Display ")').click()
    
    # # Connectivity  
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Connectivity ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Connectivity_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Connectivity_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Connectivity_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Connectivity ")').click()
    
    
    
    # # Ports & Slots  
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Ports & Slots ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Ports_Slots_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Ports_Slots_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Ports_Slots_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Ports & Slots ")').click()
    
    
    
    # # Audio 
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Audio ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Audio_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Audio_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Audio_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Audio ")').click()
    
    
    
    
    
    # # Processor  
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Processor ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Processor_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Processor_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Processor_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Processor ")').click()
    
    # # Item_details   
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Item details ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Item_details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Item_details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Item_details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Item details ")').click()
    
    # # Memory_Details   
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Memory ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Memory_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Memory_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Memory_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Memory ")').click()
    
    # # Battery_Details   
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Battery ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Battery_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Battery_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Battery_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Battery ")').click()
    
    # # Input_Details   
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Input Devices ")').click()
    # additional_details = page.locator('div.a-section table.a-keyvalue.prodDetTable tbody').first.inner_html()
    # soup = BeautifulSoup(additional_details, "html.parser")
    # all_tr = soup.find_all("tr")
    # Input_Details = {}
    # for tr in all_tr:
    #     th = tr.find("th")
    #     td = tr.find("td")
    #     Input_Details[th.get_text(strip=True)] = td.get_text(strip=True)
    # print(Input_Details)
    # page.locator('span.a-expander-prompt[role="heading"][aria-level="5"]:has-text(" Input Devices ")').click()
    
    
    
    
    
    
    
    
    
    
    
        





    page.wait_for_timeout(3000)
    browser.close()
