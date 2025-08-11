import logging
from build_dataset import build_complete_dataset
from config import FIRST_CLAN_TAG, MAX_NEW_CLANS

#logging configuration
logging.basicConfig(
    level=logging.INFO,  # ab INFO alles anzeigen
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)

if __name__ == "__main__":
    build_complete_dataset(FIRST_CLAN_TAG, MAX_NEW_CLANS)