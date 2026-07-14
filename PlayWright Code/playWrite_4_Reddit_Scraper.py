"""
Reddit Advertisement Collector using Playwright
=================================================

Logs into Reddit once (persistent browser profile), then on every subsequent
run reuses that session to scroll the home feed, detect promoted / sponsored /
suggested content, extract available fields, and export to CSV.

Usage:
    python reddit_scraper.py

First run:
    - No saved profile is found -> a visible Chromium window opens on
      reddit.com. Log in manually. Once you're logged in and the feed is
      visible, press ENTER in the terminal to save the session and continue
      (or just let the script run - it will detect the feed and proceed).

Subsequent runs:
    - The saved profile is reused automatically. No login required unless
      the session has expired, in which case the script will prompt again.

Only the standard library + playwright + pandas are required:
    pip install playwright pandas
    playwright install chromium
"""

from __future__ import annotations

import csv
import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    sync_playwright,
    Page,
    BrowserContext,
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError,
)

# 9. CONFIGURATION

CONFIG = {
    # REDDIT CREDENTIALS
    # Used only for the automated login attempt on the very first run
    # (when no saved browser_profile/ exists yet). Ignored on every subsequent run since the saved session is reused instead.
    # SECURITY NOTE: storing a plaintext password in source code.

    "REDDIT_USERNAME": "demo_user",
    "REDDIT_PASSWORD": "demo@pass",

    "HOMEPAGE_URL": "https://www.reddit.com/",
    "MAX_SCROLLS": 40,
    "SCROLL_DELAY_SECONDS": 2.0, # Wait time after each scroll before scrolling again.
    "NO_NEW_CONTENT_LIMIT": 5,       # stop after this many scrolls with no new cards
    "PROJECT_ROOT": Path(__file__).resolve().parent, # Absolute path of the folder containing the current Python file.
    "BROWSER_PROFILE_DIR": "browser_profile", # Directory where browser profile is stored.
    "OUTPUT_DIR": "output", # Folder where output files (CSV, JSON, etc.) are stored.
    "CSV_NAME": "ads.csv", 
    "LOGS_DIR": "logs", # Folder where log files are stored.
    "LOG_FILE": "scraper.log", # Name of the log file.
    "SCREENSHOTS_DIR": "screenshots", # Folder where screenshots are saved.
    "HEADLESS": False, # 
    "VIEWPORT": {"width": 1440, "height": 900}, # Browser window size (1440 × 900 pixels).
    "LOCALE": "en-US",  # Browser language/locale (en-US).
    "TIMEZONE_ID": "UTC", # Browser timezone (UTC).
    "USER_AGENT": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "NAV_TIMEOUT_MS": 30000,
    "LOGIN_WAIT_TIMEOUT_MS": 300000,  # 5 minutes to complete manual login
    "LOG_LEVEL": "INFO", # Logging level (INFO means log informational messages and above).
}


def resolve_paths(cfg: dict) -> dict:
    root = cfg["PROJECT_ROOT"]
    cfg["BROWSER_PROFILE_PATH"] = root / cfg["BROWSER_PROFILE_DIR"]
    cfg["OUTPUT_PATH"] = root / cfg["OUTPUT_DIR"]
    cfg["CSV_PATH"] = cfg["OUTPUT_PATH"] / cfg["CSV_NAME"]
    cfg["LOGS_PATH"] = root / cfg["LOGS_DIR"]
    cfg["LOG_FILE_PATH"] = cfg["LOGS_PATH"] / cfg["LOG_FILE"]
    cfg["SCREENSHOTS_PATH"] = root / cfg["SCREENSHOTS_DIR"]
    return cfg


CONFIG = resolve_paths(CONFIG)

for p in (CONFIG["BROWSER_PROFILE_PATH"], CONFIG["OUTPUT_PATH"],
          CONFIG["LOGS_PATH"], CONFIG["SCREENSHOTS_PATH"]):
    p.mkdir(parents=True, exist_ok=True)

# LOGGING

logger = logging.getLogger("reddit_ads")
logger.setLevel(getattr(logging, CONFIG["LOG_LEVEL"], logging.INFO))

_fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

_file_handler = logging.FileHandler(CONFIG["LOG_FILE_PATH"], encoding="utf-8")
_file_handler.setFormatter(_fmt)
logger.addHandler(_file_handler)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_fmt)
logger.addHandler(_console_handler)

# DATA MODEL (FR-8)

@dataclass
class AdRecord:
    # Identification
    unique_id: str = ""
    post_id: str = ""
    permalink: str = ""
    # Advertisement type
    ad_type: str = ""
    # Author
    username: str = ""
    brand_name: str = ""
    advertiser_name: str = ""
    # Community
    subreddit: str = ""
    community_url: str = ""
    # Content
    title: str = ""
    body: str = ""
    description: str = ""
    cta: str = ""
    link_text: str = ""
    destination_url: str = ""
    # Media
    image_url: str = ""
    video_url: str = ""
    thumbnail_url: str = ""
    gallery_urls: str = ""
    # Statistics
    comments: str = ""
    votes: str = ""
    awards: str = ""
    # Metadata
    timestamp: str = ""
    collected_time: str = ""
    scroll_number: int = 0
    feed_position: int = 0
    dom_index: int = 0
    # Flags
    is_promoted: bool = False
    is_suggested: bool = False
    is_sponsored: bool = False
    is_recommendation: bool = False
    is_organic: bool = False
    is_hidden: bool = False
    is_nsfw: bool = False
    is_locked: bool = False

    def dedupe_key(self) -> str:
        return (
            self.permalink
            or self.post_id
            or self.destination_url
            or f"{self.title}|{self.username}|{self.subreddit}"
        )


CSV_COLUMNS = [
    "collected_time", "ad_type", "title", "body", "description",
    "username", "brand_name", "advertiser_name",
    "subreddit", "community_url",
    "cta", "link_text", "destination_url",
    "image_url", "video_url", "thumbnail_url", "gallery_urls",
    "comments", "votes", "awards",
    "timestamp", "scroll_number", "feed_position", "dom_index",
    "is_promoted", "is_suggested", "is_sponsored", "is_recommendation",
    "is_organic", "is_hidden", "is_nsfw", "is_locked",
    "post_id", "permalink", "unique_id",
]


# --------------------------------------------------------------------------
# BROWSER SETUP  (FR-1, FR-2, FR-3)
# --------------------------------------------------------------------------

def profile_exists() -> bool:
    profile_dir = CONFIG["BROWSER_PROFILE_PATH"]
    # A fresh persistent context creates a non-trivial number of files.
    # Treat "exists" as "has been initialized before" rather than just
    # the directory being present (mkdir creates it regardless).
    return any(profile_dir.iterdir()) if profile_dir.exists() else False


def launch_browser_context(playwright) -> BrowserContext:
    """FR-3: launch persistent Chromium context with desktop settings."""
    logger.info("Launching persistent Chromium context...")
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(CONFIG["BROWSER_PROFILE_PATH"]),
        headless=CONFIG["HEADLESS"],
        viewport=CONFIG["VIEWPORT"],
        user_agent=CONFIG["USER_AGENT"],
        locale=CONFIG["LOCALE"],
        timezone_id=CONFIG["TIMEZONE_ID"],
        accept_downloads=True,
        permissions=["geolocation"],
    )
    context.set_default_navigation_timeout(CONFIG["NAV_TIMEOUT_MS"])
    context.set_default_timeout(CONFIG["NAV_TIMEOUT_MS"])
    logger.info("Browser launched.")
    return context


LOGGED_IN_SELECTOR = (
    'shreddit-app[user-logged-in="true"], '
    '[data-testid="user-drawer-button"], '
    'a[href^="/user/"]'
)


def is_logged_in(page: Page, timeout: int = 4000) -> bool:
    try:
        page.wait_for_selector(LOGGED_IN_SELECTOR, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def attempt_automated_login(page: Page) -> bool:
    """Try to log in using CONFIG['REDDIT_USERNAME'] / CONFIG['REDDIT_PASSWORD'].

    Returns True if a logged-in state was detected afterwards, False otherwise
    (e.g. Reddit threw up a CAPTCHA, 2FA prompt, or changed its login markup).
    This never attempts to solve CAPTCHAs or bypass 2FA - it simply fills the
    standard login form and lets a human take over if something extra is asked
    for.
    """
    username = CONFIG.get("REDDIT_USERNAME", "")
    password = CONFIG.get("REDDIT_PASSWORD", "")
    if not username or not password:
        return False

    logger.info("Attempting automated login for user '%s'...", username)
    try:
        page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")

        # Reddit's login form is rendered inside a shadow DOM component in
        # newer UI versions; Playwright pierces shadow roots automatically
        # for these locators.
        username_field = page.wait_for_selector(
            'input[name="username"], input#login-username', timeout=15000
        )
        password_field = page.query_selector(
            'input[name="password"], input#login-password'
        )
        if not username_field or not password_field:
            logger.warning("Login form fields not found; cannot automate login.")
            return False

        username_field.fill(username)
        password_field.fill(password)

        submit_button = page.query_selector(
            'button[type="submit"], button[data-testid="login-button"]'
        )
        if submit_button:
            submit_button.click()
        else:
            password_field.press("Enter")

        # Give Reddit a moment to process the submission / redirect.
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        if is_logged_in(page, timeout=10000):
            logger.info("Automated login succeeded.")
            return True

        logger.warning(
            "Automated login did not reach a confirmed logged-in state "
            "(Reddit may have requested CAPTCHA, 2FA, or verification)."
        )
        return False

    except Exception as e:
        logger.warning("Automated login attempt failed: %s", e)
        return False


def ensure_logged_in(page: Page, first_run: bool) -> None:
    """FR-1 / FR-2: handle first-time login (automated, with manual fallback)
    or confirm an existing restored session."""
    page.goto(CONFIG["HOMEPAGE_URL"], wait_until="domcontentloaded")

    if not first_run:
        logger.info("Existing profile detected - assuming session is restored.")
        return

    logger.info("No existing profile detected. Attempting first-time login.")

    if attempt_automated_login(page):
        return

    # Fall back to manual login - covers CAPTCHA, 2FA, unexpected UI changes,
    # or missing/incorrect credentials.
    print("\n" + "=" * 70)
    print("AUTOMATED LOGIN DID NOT COMPLETE.")
    print("A browser window is open - please log in to Reddit manually.")
    print("Once you're logged in and can see your home feed,")
    print("come back here and press ENTER to continue...")
    print("=" * 70 + "\n")

    try:
        input()
    except EOFError:
        logger.info("No interactive terminal detected; waiting for login state on page.")

    if is_logged_in(page, timeout=CONFIG["LOGIN_WAIT_TIMEOUT_MS"]):
        logger.info("Login detected.")
    else:
        logger.warning(
            "Could not positively confirm login state within timeout; "
            "proceeding anyway based on manual confirmation."
        )


# --------------------------------------------------------------------------
# FEED SCROLLING (FR-5)
# --------------------------------------------------------------------------

def scroll_feed(page: Page, max_scrolls: int, scroll_delay: float,
                 no_new_content_limit: int, on_scroll_complete) -> None:
    """Scrolls the page repeatedly, invoking on_scroll_complete(scroll_number)
    after each scroll so the caller can extract newly-loaded cards."""
    previous_height = 0
    stagnant_rounds = 0

    for scroll_number in range(1, max_scrolls + 1):
        page.mouse.wheel(0, 3000)
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        time.sleep(scroll_delay)

        current_height = page.evaluate("document.body.scrollHeight")
        new_cards_found = on_scroll_complete(scroll_number)

        if current_height == previous_height and not new_cards_found:
            stagnant_rounds += 1
            logger.info(
                "No new content on scroll %d (stagnant round %d/%d).",
                scroll_number, stagnant_rounds, no_new_content_limit,
            )
        else:
            stagnant_rounds = 0

        previous_height = current_height

        if stagnant_rounds >= no_new_content_limit:
            logger.info("No new content detected repeatedly; stopping scroll.")
            break

    logger.info("Scrolling finished.")


# --------------------------------------------------------------------------
# FEED CARD DETECTION (FR-6)
# --------------------------------------------------------------------------

FEED_CARD_SELECTORS = [
    "shreddit-post",
    "article",
    'div[data-testid="post-container"]',
    'faceplate-tracker[data-testid="feed-item"]',
]


def get_feed_cards(page: Page) -> list[ElementHandle]:
    """FR-6: gather feed item elements using multiple fallback selectors,
    de-duplicated by DOM identity."""
    seen_ids = set()
    cards: list[ElementHandle] = []

    for selector in FEED_CARD_SELECTORS:
        try:
            elements = page.query_selector_all(selector)
        except Exception:
            continue
        for el in elements:
            try:
                handle_id = el.evaluate(
                    "(el) => { "
                    "if (!el.dataset.__scraperUid) { "
                    "el.dataset.__scraperUid = Math.random().toString(36).slice(2); } "
                    "return el.dataset.__scraperUid; }"
                )
            except Exception:
                continue
            if handle_id not in seen_ids:
                seen_ids.add(handle_id)
                cards.append(el)

    return cards


# --------------------------------------------------------------------------
# ADVERTISEMENT DETECTION (FR-7)
# --------------------------------------------------------------------------

PROMOTED_PATTERNS = [
    r"\bpromoted\b",
    r"\bsponsored\b",
    r"\badvertisement\b",
]
SUGGESTED_PATTERNS = [
    r"\bsuggested\b",
    r"\brecommended\b",
    r"\bpeople you might like\b",
    r"\bcommunities you might like\b",
    r"\btrending (today|now)\b",
    r"\bbecause you\b",
]


def classify_card(card: ElementHandle) -> dict:
    """FR-7: inspect a feed card's text, aria-labels, and data attributes
    to decide whether it is promoted / sponsored / suggested / organic."""
    try:
        text_content = (card.inner_text() or "").lower()
    except Exception:
        text_content = ""

    try:
        outer_html = (card.evaluate("el => el.outerHTML") or "").lower()
    except Exception:
        outer_html = ""

    combined = f"{text_content}\n{outer_html}"

    is_promoted = any(re.search(p, combined) for p in PROMOTED_PATTERNS)
    is_suggested = any(re.search(p, combined) for p in SUGGESTED_PATTERNS)

    # Reddit also marks native ad posts with explicit attributes in many
    # UI versions - check common variants defensively.
    try:
        promoted_attr = card.evaluate(
            "el => el.getAttribute('promoted') "
            "|| el.getAttribute('data-promoted') "
            "|| (el.querySelector('[promoted]') ? 'true' : null)"
        )
    except Exception:
        promoted_attr = None

    if promoted_attr and str(promoted_attr).lower() in ("true", "1", "yes"):
        is_promoted = True

    ad_type = ""
    if is_promoted:
        ad_type = "Promoted/Sponsored"
    elif is_suggested:
        ad_type = "Suggested/Recommendation"

    return {
        "is_promoted": is_promoted,
        "is_sponsored": is_promoted,
        "is_suggested": is_suggested,
        "is_recommendation": is_suggested,
        "is_organic": not (is_promoted or is_suggested),
        "ad_type": ad_type,
    }


# --------------------------------------------------------------------------
# DATA EXTRACTION (FR-8)
# --------------------------------------------------------------------------

def safe_attr(card: ElementHandle, selector: str, attr: str) -> str:
    try:
        el = card.query_selector(selector)
        if not el:
            return ""
        val = el.get_attribute(attr)
        return val or ""
    except Exception:
        return ""


def safe_text(card: ElementHandle, selector: str) -> str:
    try:
        el = card.query_selector(selector)
        if not el:
            return ""
        return (el.inner_text() or "").strip()
    except Exception:
        return ""


def extract_ad_data(card: ElementHandle, scroll_number: int,
                     feed_position: int, dom_index: int,
                     classification: dict) -> AdRecord:
    """FR-8: pull whatever fields are available from a classified ad card."""
    record = AdRecord()

    # Identification
    record.post_id = (
        card.get_attribute("id")
        or card.get_attribute("data-post-id")
        or card.get_attribute("data-testid")
        or ""
    )
    permalink = card.get_attribute("permalink") or card.get_attribute("href") or ""
    if not permalink:
        link_el = card.query_selector('a[href*="/comments/"], a[data-click-id="body"]')
        if link_el:
            permalink = link_el.get_attribute("href") or ""
    record.permalink = (
        f"https://www.reddit.com{permalink}"
        if permalink.startswith("/")
        else permalink
    )

    # Author / brand
    record.username = (
        card.get_attribute("author")
        or safe_text(card, '[data-testid="post_author_link"]')
        or safe_text(card, 'a[href^="/user/"]')
    )
    record.brand_name = record.username
    record.advertiser_name = record.username

    # Community
    record.subreddit = card.get_attribute("subreddit-prefixed-name") or safe_text(
        card, 'a[href^="/r/"]'
    )
    if record.subreddit and not record.subreddit.startswith("r/"):
        record.subreddit = f"r/{record.subreddit}"
    community_href = safe_attr(card, 'a[href^="/r/"]', "href")
    record.community_url = (
        f"https://www.reddit.com{community_href}" if community_href else ""
    )

    # Content
    record.title = card.get_attribute("post-title") or safe_text(
        card, 'h3, [slot="title"], [data-testid="post-title"]'
    )
    record.body = safe_text(card, '[data-testid="post-content"], [slot="text-body"]')
    record.description = record.body[:280] if record.body else ""

    cta_el = card.query_selector('a[data-testid="outbound-link"], a[slot="cta"], button[data-testid="cta"]')
    if cta_el:
        record.cta = (cta_el.inner_text() or "").strip()
        record.link_text = record.cta
        record.destination_url = cta_el.get_attribute("href") or ""

    # Media
    img_el = card.query_selector("img")
    if img_el:
        record.image_url = img_el.get_attribute("src") or ""
        record.thumbnail_url = img_el.get_attribute("data-thumbnail") or record.image_url

    video_el = card.query_selector("video, shreddit-player")
    if video_el:
        record.video_url = (
            video_el.get_attribute("src")
            or video_el.get_attribute("preview")
            or ""
        )

    gallery_els = card.query_selector_all('[data-testid="gallery"] img, ul.gallery img')
    if gallery_els:
        urls = [g.get_attribute("src") for g in gallery_els if g.get_attribute("src")]
        record.gallery_urls = json.dumps(urls)

    # Statistics
    record.comments = card.get_attribute("comment-count") or safe_text(
        card, '[data-testid="comments-page-link-num-comments"]'
    )
    record.votes = card.get_attribute("score") or safe_text(
        card, '[data-testid="vote-arrows"]'
    )
    record.awards = safe_text(card, '[data-testid="awards"]')

    # Metadata
    record.timestamp = card.get_attribute("created-timestamp") or safe_attr(
        card, "time", "datetime"
    )
    record.collected_time = datetime.utcnow().isoformat() + "Z"
    record.scroll_number = scroll_number
    record.feed_position = feed_position
    record.dom_index = dom_index

    # Flags
    record.is_promoted = classification["is_promoted"]
    record.is_sponsored = classification["is_sponsored"]
    record.is_suggested = classification["is_suggested"]
    record.is_recommendation = classification["is_recommendation"]
    record.is_organic = classification["is_organic"]
    record.ad_type = classification["ad_type"]
    record.is_nsfw = (card.get_attribute("nsfw") or "").lower() == "true"
    record.is_locked = (card.get_attribute("locked") or "").lower() == "true"
    record.is_hidden = (card.get_attribute("hidden") or "").lower() == "true"

    record.unique_id = record.dedupe_key()

    return record


# --------------------------------------------------------------------------
# CSV EXPORT (FR-9) + DUPLICATE DETECTION (FR-10)
# --------------------------------------------------------------------------

class AdCollector:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.seen_keys: set[str] = set()
        self._load_existing_keys()
        self._ensure_header()

    def _load_existing_keys(self) -> None:
        if not self.csv_path.exists():
            return
        try:
            with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = row.get("permalink") or row.get("post_id") or row.get("unique_id")
                    if key:
                        self.seen_keys.add(key)
        except Exception as e:
            logger.warning("Could not read existing CSV for dedup keys: %s", e)

    def _ensure_header(self) -> None:
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()

    def add(self, record: AdRecord) -> bool:
        """Returns True if the record was new and written, False if duplicate."""
        key = record.dedupe_key()
        if key in self.seen_keys:
            return False
        self.seen_keys.add(key)
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                row = asdict(record)
                writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})
        except Exception as e:
            logger.error("Failed to write record to CSV: %s", e)
            return False
        return True


# --------------------------------------------------------------------------
# ERROR HANDLING / SCREENSHOTS (FR-12)
# --------------------------------------------------------------------------

def capture_error_screenshot(page: Page, label: str) -> None:
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        path = CONFIG["SCREENSHOTS_PATH"] / f"error_{label}_{timestamp}.png"
        page.screenshot(path=str(path))
        logger.info("Screenshot saved: %s", path)
    except Exception as e:
        logger.warning("Could not capture screenshot: %s", e)


# --------------------------------------------------------------------------
# MAIN WORKFLOW (Section 10)
# --------------------------------------------------------------------------

def run() -> None:
    logger.info("=" * 60)
    logger.info("Reddit Advertisement Collector - starting run")
    logger.info("=" * 60)

    first_run = not profile_exists()
    collector = AdCollector(CONFIG["CSV_PATH"])
    total_found = 0
    total_saved = 0

    with sync_playwright() as playwright:
        context = None
        try:
            context = launch_browser_context(playwright)
            logger.info("Profile loaded from %s", CONFIG["BROWSER_PROFILE_PATH"])

            page = context.pages[0] if context.pages else context.new_page()

            ensure_logged_in(page, first_run=first_run)

            logger.info("Navigating to homepage: %s", CONFIG["HOMEPAGE_URL"])
            page.goto(CONFIG["HOMEPAGE_URL"], wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                logger.warning("networkidle wait timed out on homepage load; continuing.")

            def process_new_cards(scroll_number: int) -> bool:
                nonlocal total_found, total_saved
                cards = get_feed_cards(page)
                new_this_round = 0

                for dom_index, card in enumerate(cards):
                    try:
                        classification = classify_card(card)
                        if not (classification["is_promoted"] or classification["is_suggested"]):
                            continue

                        total_found += 1
                        record = extract_ad_data(
                            card,
                            scroll_number=scroll_number,
                            feed_position=total_found,
                            dom_index=dom_index,
                            classification=classification,
                        )
                        if collector.add(record):
                            total_saved += 1
                            new_this_round += 1
                            logger.info(
                                "Ad captured [%s] title=%r subreddit=%r",
                                record.ad_type, record.title[:60], record.subreddit,
                            )
                    except Exception as e:
                        logger.error("Failed to process a feed card: %s", e)
                        capture_error_screenshot(page, "card_extract")
                        continue

                return new_this_round > 0

            logger.info("Beginning feed scroll...")
            scroll_feed(
                page,
                max_scrolls=CONFIG["MAX_SCROLLS"],
                scroll_delay=CONFIG["SCROLL_DELAY_SECONDS"],
                no_new_content_limit=CONFIG["NO_NEW_CONTENT_LIMIT"],
                on_scroll_complete=process_new_cards,
            )

            logger.info(
                "Run complete. Ads/suggested items found: %d, new records saved: %d",
                total_found, total_saved,
            )
            logger.info("CSV saved at: %s", CONFIG["CSV_PATH"])

        except Exception as e:
            logger.error("Unhandled error during run: %s", e, exc_info=True)
            if context and context.pages:
                capture_error_screenshot(context.pages[0], "fatal")
        finally:
            if context:
                context.close()
            logger.info("Browser context closed. Execution completed.")




if __name__ == "__main__":
    run()

