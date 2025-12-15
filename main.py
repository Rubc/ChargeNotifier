import os
import requests
import time
import urllib.parse
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_URL = "https://dieterenenergy.evc-net.com/api/ajax"

# Configure the device IDs you want to monitor
DEVICE_IDS = [155620231, 155620232]
# Build the request payload
REQUESTS_PAYLOAD = {
    "0": {
        "handler": "\\LMS\\EV\\AsyncServices\\DashboardAsyncService",
        "method": "spotsStatusPointData",
        "params": {
            "deviceIds": DEVICE_IDS
        }
    }
}

encoded_requests = urllib.parse.quote(json.dumps(REQUESTS_PAYLOAD))
API_URL = f"{BASE_URL}?requests={encoded_requests}"

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

INTERVAL = 300  # seconds

last_status = {}

STATUS_MAP = {
    1: "Available",
    3: "Charging"
}

def send_discord_message(content: str):
    payload = {"content": content}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_status():
    global last_status
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            for sublist in data:
                if isinstance(sublist, list):
                    for device in sublist:
                        device_id = device.get("id")
                        status_code = device.get("globalStatus")
                        name = device.get("physicalNumber")

                        if device_id is None or status_code is None:
                            continue

                        status_text = STATUS_MAP.get(status_code, f"Unknown ({status_code})")

                        if last_status.get(device_id) != status_code:
                            message = f"Device {device_id} ({name}) status changed to: {status_text}"
                            print(message)
                            send_discord_message(message)

                        last_status[device_id] = status_code

    except Exception as e:
        print(f"Error fetching/parsing API: {e}")

def main():
    while True:
        check_status()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
