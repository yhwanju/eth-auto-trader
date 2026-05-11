import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_message(message):

    data = {
        "content": message
    }

    requests.post(WEBHOOK_URL, json=data)
    