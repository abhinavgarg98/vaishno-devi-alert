
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
    dates = fetch_dates()
    previous = None

    if STATE_FILE.exists():
        previous = json.loads(STATE_FILE.read_text())

    # First run establishes a baseline and sends a report.
    if previous is None or dates != previous:
        if dates:
            body = "\n".join(f"• {date}" for date in dates)
        else:
            body = "No available calendar dates were returned."

        send_telegram(
            "🔔 Vaishno Devi accommodation calendar\n\n"
            f"Available dates: {len(dates)}\n\n{body}\n\n"
            "Calendar dates do not guarantee private-room inventory. "
            "Please verify on the official website."
        )
        print(f"Availability list changed; {len(dates)} dates reported.")
    else:
        print("Availability list unchanged.")

    STATE_FILE.write_text(json.dumps(dates))


if __name__ == "__main__":
    main()
