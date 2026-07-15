import os
import requests
from bs4 import BeautifulSoup

BMS_URL = "https://in.bookmyshow.com/movies/chennai/the-odyssey/buytickets/ET00480917/20260720"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": False
    }, timeout=20)

def main():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(BMS_URL, headers=headers, timeout=25)
    html = r.text.lower()

    # Booking is likely open if the 20 July page contains actual cinema/showtime data.
    booking_signals = [
        "pvr",
        "inox",
        "imax",
        "available",
        "fast filling",
        "non-cancellable"
    ]

    has_show_signal = any(signal in html for signal in booking_signals)

    # Avoid repeated alerts after first success
    if has_show_signal:
        send_alert(
            "🚨 ODYSSEY BOOKING OPEN!\n\n20 July shows may be live on BookMyShow.\nBook now:\n"
            + BMS_URL
        )
        print("Booking appears open. Alert sent.")
    else:
        print("Still not open.")

if __name__ == "__main__":
    main()
