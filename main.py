import requests
import time

API_URL = "https://dieterenenergy.evc-net.com/api/ajax?requests=%7B%220%22%3A%7B%22handler%22%3A%22%5C%5CLMS%5C%5CEV%5C%5CAsyncServices%5C%5CDashboardAsyncService%22%2C%22method%22%3A%22spotsStatusPointData%22%2C%22params%22%3A%7B%22deviceIds%22%3A%5B155620231%2C155620232%5D%2C%22tariffProvider%22%3A295%7D%7D%7D&metricKey=DeviceMap_1037"

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1448064495090925711/n7JONb8lRxU4ATfduddwOKngpysE2Bx4FsC3W75njWpJd48I3i0olyMQ4BBF04tYEwgP"

INTERVAL = 60  # seconds

last_status = {}

# Map numeric codes to human-readable states
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

        # The response is [[{...}, {...}]]
        if isinstance(data, list):
            for sublist in data:
                if isinstance(sublist, list):
                    for device in sublist:
                        device_id = device.get("id")
                        status_code = device.get("globalStatus")
                        name = device.get("physicalNumber")

                        if device_id is None or status_code is None:
                            continue

                        # Translate status code
                        status_text = STATUS_MAP.get(status_code, f"Unknown ({status_code})")

                        # Compare with last known status
                        if last_status.get(device_id) != status_code:
                            message = f"Device {device_id} ({name}) status changed to: {status_text}"
                            print(message)
                            send_discord_message(message)

                        # Update stored status
                        last_status[device_id] = status_code

    except Exception as e:
        print(f"Error fetching/parsing API: {e}")

def main():
    while True:
        check_status()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
