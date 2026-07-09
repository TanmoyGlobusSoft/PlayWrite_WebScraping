from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False, 
        
    )

    page = browser.new_page()

    page.goto("https://www.amazon.in/")

    page.locator("input#twotabsearchtextbox").fill("iphone")

    page.locator('input[type="submit"]').click()

    page.locator('button[id="a-autoid-3-announce"]').click()
    page.wait_for_timeout(5000)
    browser.close()