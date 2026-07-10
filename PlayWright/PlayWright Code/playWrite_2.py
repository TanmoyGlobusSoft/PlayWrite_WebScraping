from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
from bs4 import BeautifulSoup
import json
import sqlite3


def get_details(n):
    details = page.locator("div.a-section table.a-keyvalue.prodDetTable tbody")
    # print(details.count())
    # print(details.nth(n-1).inner_html())
    if details.count() >= n - 1:
        details = details.nth(n - 1).inner_html()
        soup = BeautifulSoup(details, "html.parser")
        all_tr = soup.find_all("tr")
        Details_dict = {}
        for tr in all_tr:
            th = tr.find("th")
            td = tr.find("td")
            Details_dict[th.get_text(strip=True)] = td.get_text(strip=True)
        return json.dumps(Details_dict)
    return None


conn = sqlite3.connect("AmazonProducts.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Laptop_Data(
        Product_ASIN TEXT PRIMARY KEY,
        Product_Name TEXT,
        Brand TEXT,
        Price TEXT,
        Rating TEXT,
        Reviews TEXT,
        Image_URLs TEXT,
        Product_Details TEXT,
        Brand_Details TEXT,
        Additional_Details TEXT,
        Display_Details TEXT,
        Connectivity_Details TEXT,
        Ports_Slots_Details TEXT,
        Audio_Details TEXT,
        Processor_Details TEXT,
        Item_details TEXT,
        Memory_Details TEXT,
        Battery_Details TEXT,
        Input_Details TEXT
    );
""")
conn.commit()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    # browser = p.chromium.launch()

    page = browser.new_page()

    ASIN = ["B0DB218DK7", "B0FM3C4L2F", "B096XZH2W4", "B0GSVMFC9Z", "B0D2299GB9", "B0D5DH91HV", "B096Y66WF9", "B0DFLQZMJD", "B0F8RB221J", "B0C918JGBM", "B0CV427854", "B0GX4W73SM", "B0FK8QVFJ5", "B0GP7BRZR6", "B0G48KV4YP", "B0CX8RYYVR", "B0DB218DK7", "B0GVRZD89W"]
    # ASIN = ["B0DB218DK7"]

    for asin in ASIN:
        page.goto(f"https://www.amazon.in/_/dp/{asin}")

        ### Phase 4 — Data Extraction
        Product_ASIN = asin

        Product_Name = page.locator("#productTitle").nth(0).text_content().strip()
        # print(Product_Name)

        Brand = page.locator('tr:has-text("Brand") td').nth(1).inner_text()
        # print(Brand)

        Price = page.locator("span.a-price-whole").nth(1).inner_text()
        # print(Price)

        Rating = (
            page.locator('span.a-icon-alt:has-text("out of 5 stars")')
            .nth(1)
            .inner_text()
        )
        # print(Rating)

        # Reviews
        Reviews = page.locator("span#acrCustomerReviewText").nth(0).inner_text()
        # print(Reviews)

        # Image URL's
        Images = page.locator("span.a-button-text[id^='a-autoid-'] img")
        Image_URLs = ""
        for img in range(Images.count()):
            Image_URLs += ", " + Images.nth(img).get_attribute("src")
        Image_URLs = json.dumps(Image_URLs)
        # print(Image_URLs)

        # Product Details
        product_details = page.locator(
            "table.a-normal.a-spacing-micro[role='list'] tbody"
        ).inner_html()
        soup = BeautifulSoup(product_details, "html.parser")
        all_tr = soup.find_all("tr")
        Product_Details = {}
        for tr in all_tr:
            td = tr.find_all("td")
            # print(td[0].get_text(strip=True), " >><< ", td[1].get_text(strip=True))
            Product_Details[td[0].get_text(strip=True)] = td[1].get_text(strip=True)
        Product_Details = json.dumps(Product_Details)
        # print(Product_Details)

        # Brand Details
        Brand_Details = page.locator(
            "div.a-section.a-spacing-base.brand-snapshot-flex-row[role='listitem']"
        ).all_text_contents()
        Brand_Details = ", ".join(Brand_Details)
        # print(brand_details)

        # Additional Details
        Additional_Details = get_details(0)
        # print(Additional_Details)

        # Display Details
        Display_Details = get_details(1)
        # print(Display_Details)

        # Connectivity Details
        Connectivity_Details = get_details(2)
        # print(Connectivity_Details)

        # Ports & Slots Details
        Ports_Slots_Details = get_details(3)
        # print(Ports_Slots_Details)

        # Audio Details
        Audio_Details = get_details(4)
        # print(Audio_Details)

        # Processor Details
        Processor_Details = get_details(5)
        # print(Processor_Details)

        # Item details
        Item_details = get_details(6)
        # print(Item_details)

        # Memory Details
        Memory_Details = get_details(7)
        # print(Memory_Details)

        # Battery Details
        Battery_Details = get_details(8)
        # print(Battery_Details)

        # Input_Details
        Input_Details = get_details(9)
        # print(Input_Details)

        cursor.execute("""
            INSERT OR REPLACE INTO Laptop_Data(Product_ASIN, Product_Name , Brand , Price , Rating , Reviews , Image_URLs , Product_Details , Brand_Details , Additional_Details , Display_Details , Connectivity_Details , Ports_Slots_Details , Audio_Details , Processor_Details , Item_details , Memory_Details , Battery_Details , Input_Details) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); 
            """, 
            (Product_ASIN, Product_Name, Brand, Price, Rating, Reviews, Image_URLs, Product_Details, Brand_Details, Additional_Details, Display_Details, Connectivity_Details, Ports_Slots_Details, Audio_Details, Processor_Details, Item_details, Memory_Details, Battery_Details, Input_Details)
        )
        conn.commit()

    # page.wait_for_timeout(3000)
    browser.close()

cursor.execute("SELECT * FROM Laptop_Data")
row = cursor.fetchall()
print(len(row)) 