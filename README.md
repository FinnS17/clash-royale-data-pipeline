# Clash Royale Data Pipeline

Reproducible pipeline to ingest Clash Royale battle logs via the official Clash Royale API, store them efficiently in Parquet format, and incrementally resume collection using a visited-clans checkpoint system.

## 🚀 Quickstart
1. **Create and activate a virtual environment**  
   python3 -m venv venv && source venv/bin/activate

2. **Install dependencies**  
   pip install -r requirements.txt

3. **Set your API token**  
   cp .env.example .env  
   # Then edit .env and set CLASH_API_TOKEN

4. **Run the main script**  
   python main.py

## ⚙️ Configuration
- **Secret config:** `.env` → `CLASH_API_TOKEN`
- **Public config:** `config.py` → `FIRST_CLAN_TAG`, `MAX_NEW_CLANS`, etc.

## 📦 Outputs
- `data/clash_battles.parquet` — main dataset in Parquet format
- `checkpoints/visited_clans.json` — list of already-processed clans for incremental runs

## ✨ Features
- Automatic retry & rate-limit handling
- Incremental scraping without revisiting processed clans
- Efficient storage and reload via Parquet format
- Logging for progress tracking and error reporting

## 📝 Notes
- Requires a valid Clash Royale API token from [developer.clashroyale.com](https://developer.clashroyale.com)
- This project collects only metadata for analysis; no copyrighted game assets are stored.