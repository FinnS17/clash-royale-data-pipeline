import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("CLASH_API_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {token}"
}

BASE_URL = "https://api.clashroyale.com/v1"

MAX_RETRIES = 3










