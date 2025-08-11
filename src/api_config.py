"""
API configuration for Clash Royale data collection.

Loads the Clash Royale API token from a `.env` file and defines
shared constants for authentication and request settings.

Variables:
    HEADERS (dict): Authorization header with Bearer token.
    BASE_URL (str): Base endpoint for Clash Royale API requests.
    MAX_RETRIES (int): Number of retry attempts for failed requests.
    TIMEOUT_SECS (int): Timeout for HTTP requests in seconds.

Note:
    Ensure you have set `CLASH_API_TOKEN` in your `.env` file before running.
"""
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("CLASH_API_TOKEN")
assert token, "Please set CLASH_API_TOKEN in your .env"

HEADERS = {
    "Authorization": f"Bearer {token}"
}

BASE_URL = "https://api.clashroyale.com/v1"

MAX_RETRIES = 3
TIMEOUT_SECS = 30










