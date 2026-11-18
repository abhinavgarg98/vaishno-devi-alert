
import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

API_URL = (
    "https://online.maavaishnodevi.org/"
    "api/v1/eAccommodation/accomSummary"
)

# Target date: 6 December 2026
TARGET_DATE = "2026-12-06"

# Exotel configuration
EXOTEL_API_URL = (
    "https://api.exotel.com/v1/Accounts/"
    "rnmotors1/Calls/connect"
)

EXOTEL_CALLER_ID = "08047291129"

EXOTEL_FLOW_URL = (
    "http://my.exotel.com/rnmotors1/"
    "exoml/start_voice/1390169"
)


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


def make_exotel_call():
    api_key = os.environ["EXOTEL_API_KEY"]
    api_token = os.environ["EXOTEL_API_TOKEN"]
    phone_number = os.environ["EXOTEL_PHONE_NUMBER"]

    payload = {
        "From": phone_number,
        "CallerId": EXOTEL_CALLER_ID,
        "CallType": "trans",
        "Url": EXOTEL_FLOW_URL,
        "TimeLimit": 60,
        "TimeOut": 30,
    }

    response = requests.post(
        EXOTEL_API_URL,
        auth=HTTPBasicAuth(api_key, api_token),
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data=payload,
        timeout=30,
    )

    response.raise_for_status()

    print("Exotel call request submitted successfully.")
    print("Exotel response:", response.text)


def normalize_date(date_value):
    """Convert supported date formats to YYYY-MM-DD."""

    date_value = str(date_value).strip()

    for date_format in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(
                date_value, date_format
            ).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


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

    if not isinstance(data, dict):
        raise ValueError("API returned an invalid response")

    dates = data.get("availableDatesList")

    if not isinstance(dates, list):
        raise ValueError(
            "API response did not contain a valid availableDatesList"
        )

    return sorted(set(str(date) for date in dates))


def main():
    try:
        dates = fetch_dates()

    except Exception as e:
        message = (
            "⚠️ Vaishno Devi Accommodation API Failed\n\n"
            "Please check the official website manually.\n\n"
            f"Error: {str(e)[:500]}"
        )

        try:
            send_telegram(message)
        finally:
            raise

    # ORIGINAL TELEGRAM LOGIC - UNCHANGED
    if not dates:
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

    # EXOTEL LOGIC - ONLY FOR 6 DECEMBER 2026
    target_available = any(
        normalize_date(date) == TARGET_DATE
        for date in dates
    )

    if target_available:
        print(
            "6 December 2026 found! "
            "Triggering Exotel phone call."
        )

        try:
            make_exotel_call()

        except Exception as e:
            print("Exotel call failed:", str(e))

            try:
                send_telegram(
                    "⚠️ 6 December 2026 is available, "
                    "but Exotel call failed.\n\n"
                    f"Error: {str(e)[:400]}"
                )
            except Exception as telegram_error:
                print(
                    "Failed to send Exotel error notification:",
                    str(telegram_error)
                )

    else:
        print(
            "6 December 2026 not available. "
            "No Exotel call."
        )


if __name__ == "__main__":
    main()
