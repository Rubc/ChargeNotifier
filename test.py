import requests

# Replace with your actual webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1448064495090925711/n7JONb8lRxU4ATfduddwOKngpysE2Bx4FsC3W75njWpJd48I3i0olyMQ4BBF04tYEwgP"

def send_test_message():
    payload = {"content": "🚀 Test message from Proxmox script — webhook is working!"}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

    if response.status_code == 204:
        print("✅ Message sent successfully to Discord")
    else:
        print(f"❌ Failed to send message: {response.status_code}, {response.text}")

if __name__ == "__main__":
    send_test_message()
