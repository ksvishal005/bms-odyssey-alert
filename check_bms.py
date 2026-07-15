import os
import sys
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

BMS_URL = "https://in.bookmyshow.com/movies/chennai/the-odyssey/buytickets/ET00480917/20260720"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SCREENSHOT_PATH = Path("bms_odyssey_20_july.png")


def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    ).raise_for_status()


def send_telegram_photo(message: str, photo_path: Path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with photo_path.open("rb") as photo:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": message,
            },
            files={"photo": photo},
            timeout=30,
        ).raise_for_status()


def page_looks_bookable(page) -> bool:
    body_text = page.locator("body").inner_text(timeout=15000).lower()

    closed_signals = [
        "no shows available",
        "no cinemas available",
        "sorry, no shows available",
        "coming soon",
        "not available",
        "no showtimes available",
    ]

    if any(signal in body_text for signal in closed_signals):
        return False

    # Real showtime buttons usually look like 09:30 AM, 10:45 PM, etc.
    time_buttons = page.locator(
        "text=/\\b(0?[1-9]|1[0-2]):[0-5][0-9]\\s?(AM|PM)\\b/i"
    )

    count = time_buttons.count()
    print(f"Detected showtime-like buttons/text count: {count}")

    if count >= 1:
        return True

    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        print(f"Opening: {BMS_URL}")
        page.goto(BMS_URL, wait_until="domcontentloaded", timeout=60000)

        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            print("Network idle timeout; continuing anyway.")

        page.wait_for_timeout(5000)
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)

        if page_looks_bookable(page):
            message = (
                "🚨 ODYSSEY BOOKING MAY BE OPEN!\n\n"
                "20 July 2026 shows seem to be visible/bookable on BookMyShow.\n\n"
                f"Book now:\n{BMS_URL}"
            )
            send_telegram_message(message)
            print("Booking appears open. Telegram alert sent.")
            sys.exit(0)

        print("Still not open / no bookable show detected.")
        browser.close()


if __name__ == "__main__":
    main()
