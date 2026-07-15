import os
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

START_URL = "https://in.bookmyshow.com/movies/chennai/the-odyssey/buytickets/ET00480917/20260719"
TARGET_DATE_URL_PART = "20260720"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SCREENSHOT_PATH = Path("bms_odyssey_20_july.png")


def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()


def send_telegram_photo(message: str, photo_path: Path):
    if not photo_path.exists() or photo_path.stat().st_size == 0:
        send_telegram_message(message)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with photo_path.open("rb") as photo:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": message,
            },
            files={
                "photo": ("bms_odyssey_20_july.png", photo, "image/png")
            },
            timeout=30,
        )

    if response.status_code != 200:
        send_telegram_message(message)
        return

    response.raise_for_status()


def has_showtimes(page) -> bool:
    try:
        body_text = page.locator("body").inner_text(timeout=15000).lower()
    except Exception:
        return False

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

    # Detect actual showtime text like 09:30 AM, 7:15 PM, etc.
    try:
        time_slots = page.locator(
            "text=/\\b(0?[1-9]|1[0-2]):[0-5][0-9]\\s?(AM|PM)\\b/i"
        )
        return time_slots.count() > 0
    except Exception:
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

        try:
            page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            page.wait_for_timeout(5000)

            # Find visible 20 July date tile.
            date_tile = page.locator("text=/\\b20\\b/").first()

            if date_tile.count() == 0:
                print("not open")
                browser.close()
                return

            try:
                date_tile.click(timeout=5000)
                page.wait_for_timeout(5000)
            except Exception:
                print("not open")
                browser.close()
                return

            current_url = page.url

            page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)

            booking_open = (
                TARGET_DATE_URL_PART in current_url
                or has_showtimes(page)
            )

            if booking_open:
                message = (
                    "🚨🚨🚨 BOOKING OPEN 🚨🚨🚨\n\n"
                    "ODYSSEY 20 JULY TICKETS MAY BE OPEN!\n\n"
                    "BOOK IMMEDIATELY:\n"
                    f"{current_url}"
                )

                send_telegram_photo(message, SCREENSHOT_PATH)
                print("BOOKING OPEN")
            else:
                print("not open")

        except Exception:
            print("not open")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
