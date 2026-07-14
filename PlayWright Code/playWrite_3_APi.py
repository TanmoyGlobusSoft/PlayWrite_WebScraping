import os
import json
import urllib.parse
from playwright.sync_api import sync_playwright

def main():
    url = "https://www.amazon.in/Lenovo-IdeaPad-Next-Gen-Keyboard-83UR009QIN/dp/B0H3PV7418/?_encoding=UTF8&ref_=pd_hp_d_atf_dealz_cs"
    abs_path = os.path.abspath(__file__)  # f:\Learning\PlayWrite\AI Code\main.py
    dir_name = os.path.dirname(abs_path)  # f:\Learning\PlayWrite\AI Code
    output_dir = os.path.join(dir_name, "output")  # f:\Learning\PlayWrite\AI Code\output

    # os.makedirs() → Creates the directory
    # exist_ok=True → Don't raise an error if the directory already exists.
    os.makedirs(output_dir, exist_ok=True)
    
    # Intercepted APIs means capturing or monitoring the API requests and responses that a website sends and receives.
    intercepted_apis = []
    api_counter = 0

    def handle_response(response):
        # nonlocal is used inside a nested (inner) function when you want to modify a variable that belongs to the outer function.
        # Without nonlocal, Python assumes you're creating a new local variable inside the inner function.
        # nonlocal allows a function to read and modify a variable from its immediately enclosing (outer) function, instead of creating a new local variable.
        nonlocal api_counter
        try:
            request = response.request
            resource_type = request.resource_type
            
            # Get response content type
            content_type = response.headers.get("content-type", "").lower()
            
            # Check if this request is fetch/xhr or has a JSON content-type
            if "json" in content_type or resource_type in ["fetch", "xhr"]:
                # Only check successful response statuses
                if 200 <= response.status < 300:
                    try:
                        # Attempt to parse response as JSON
                        json_data = response.json()
                    except Exception:
                        # Not a valid JSON payload or unable to read
                        return
                    
                    api_counter += 1
                    req_url = response.url
                    
                    # Store details of the API call
                    api_info = {
                        "id": api_counter,
                        "url": req_url,
                        "method": request.method,
                        "status": response.status,
                        "resource_type": resource_type,
                        "content_type": content_type,
                        "request_headers": dict(request.headers),
                        "request_post_data": request.post_data,
                        "response_file": f"api_response_{api_counter}.json"
                    }
                    
                    # Save response payload to a separate file
                    response_filename = f"api_response_{api_counter}.json"
                    response_filepath = os.path.join(output_dir, response_filename)
                    with open(response_filepath, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2)
                        
                    intercepted_apis.append(api_info)
                    
                    # Print brief info to the console
                    parsed_url = urllib.parse.urlparse(req_url)
                    url_path = parsed_url.path
                    if parsed_url.query:
                        url_path += f"?{parsed_url.query[:30]}..."
                    print(f"[{api_counter}] Captured JSON response from: {parsed_url.netloc}{url_path}")
                    
        except Exception:
            # Silently ignore errors during network interception (e.g. connections closed early)
            pass

    print(f"Starting Playwright and navigating to Amazon URL...")
    
    with sync_playwright() as p:
        # Launch headed browser to handle potential Captchas and let the user see it
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Set a realistic desktop User Agent
        context = browser.new_context(
            # Sets the User-Agent string that the browser sends with every HTTP request.
            # Without setting it, Playwright uses its own default User-Agent, which may reveal automation.
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Sets the browser window size.
            viewport={"width": 1280, "height": 800}
        )
        
        # create a new tab in our browser instent
        page = context.new_page()
        
        # Attach response listener
        page.on("response", handle_response)
        
        # Navigate to target Amazon page
        print(f"Navigating to: {url}")
        page.goto(url, wait_until="load", timeout=60000)
        
        # Check for CAPTCHA
        captcha_selector = "input[placeholder='Type characters']"
        captcha_visible = False
        try:
            captcha_visible = page.locator(captcha_selector).is_visible()
        except Exception:
            pass
            
        if "captcha" in page.title().lower() or captcha_visible:
            print("\n" + "="*60)
            print("WARNING: Amazon Captcha page detected!")
            print("Please solve the captcha in the opened Chromium browser window...")
            print("="*60 + "\n")
            
            # Wait until captcha page is solved
            while True:
                page.wait_for_timeout(1000)
                try:
                    title_lower = page.title().lower()
                    captcha_still_visible = page.locator(captcha_selector).is_visible()
                    if "captcha" not in title_lower and not captcha_still_visible:
                        print("Captcha resolved! Continuing execution...")
                        break
                except Exception:
                    break
        
        # Wait a moment after page load
        page.wait_for_timeout(3000)
        
        # Scroll page slowly to trigger lazy loading APIs (reviews, specs, suggestions, etc.)
        print("Scrolling page to trigger API calls...")
        scroll_steps = 12
        for step in range(1, scroll_steps + 1):
            fraction = step / scroll_steps
            print(f"Scrolling progress: {int(fraction * 100)}%")
            page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {fraction});")
            page.wait_for_timeout(1500)
            
        # Scroll back up a bit and wait to capture any remaining delayed XHRs
        page.evaluate("window.scrollTo(0, 0);")
        print("Waiting for any pending background API requests to finish...")
        page.wait_for_timeout(5000)
        
        # Save the summary of all API calls
        summary_filepath = os.path.join(output_dir, "api_calls_summary.json")
        with open(summary_filepath, "w", encoding="utf-8") as f:
            json.dump(intercepted_apis, f, indent=2)
            
        print("\n" + "="*50)
        print(f"Done! Captured {len(intercepted_apis)} API requests.")
        print(f"Summary saved to: {summary_filepath}")
        print(f"Detailed JSON responses are in: {output_dir}")
        print("="*50 + "\n")
        
        browser.close()

if __name__ == "__main__":
    main()
