"""
Main entry point for building the Clash Royale battle dataset.

This script initializes logging and triggers the dataset-building
pipeline starting from a given clan tag. The script uses the 
Clash Royale API to collect battle data and expand it through
discovery of new clans.

Execution:
    python main.py

Requires:
    - config.py with FIRST_CLAN_TAG and MAX_NEW_CLANS set
    - build_dataset module with `build_complete_dataset` function
"""

import logging
from build_dataset import build_complete_dataset
from config import FIRST_CLAN_TAG, MAX_NEW_CLANS

# Logging configuration
logging.basicConfig(
    level=logging.INFO,  # show all messages from INFO level upwards
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)

if __name__ == "__main__":
    build_complete_dataset(FIRST_CLAN_TAG, MAX_NEW_CLANS)