
import json
import os
from pathlib import Path

import requests

API_URL = (
    "https://online.maavaishnodevi.org/"
    "api/v1/eAccommodation/accomSummary"
)
STATE_FILE = Path("previous_dates.json")


def send_telegram(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=20,
    )
    response.raise_for_status()


def fetch_dates():
    token = os.environ["SHRINE_AUTH_TOKEN"]
    cookie = os.environ.get("SHRINE_COOKIE", "")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:156.0) "
            "Gecko/20100101 Firefox/156.0"
        ),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://online.maavaishnodevi.org",
        "Referer": "https://online.maavaishnodevi.org/",
        "tof-auth-token": token,
    }
    if cookie:
        headers["Cookie"] = cookie

    response = requests.post(
        API_URL,
        headers=headers,
        json={"locationId": "3", "accomTypeId": "1"},
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    dates = data.get("availableDatesList")
    if not isinstance(dates, list):
        raise ValueError("API response did not contain availableDatesList")

    return sorted(set(str(date) for date in dates))



def main():
    try:
        dates = fetch_dates()
    except Exception as e:
        message = (
            "⚠️ Vaishno Devi Accommodation API Failed\n\n"
            "The API request failed or returned an invalid response.\n"
            "Please check the official website manually.\n\n"
            f"Error: {str(e)[:500]}"
        )
        send_telegram(message)
        raise

    if len(dates) == 0:
        print("No available dates. No Telegram message sent.")
        return

    date_text = "\n".join(f"• {date}" for date in dates)

    message = (
        "🔔 Vaishno Devi Accommodation Calendar\n\n"
        f"Available dates: {len(dates)}\n\n"
        f"{date_text}\n\n"
        "Please verify room category and inventory "
        "on the official website."
    )

    send_telegram(message)
    print(f"Sent {len(dates)} available dates to Telegram.")


if __name__ == "__main__":
    main()

