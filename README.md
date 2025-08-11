# 📊 Clash Royale Data Pipeline

This repository builds a clean, analysis-ready **DataFrame of Clash Royale matches** that includes, per match, the **player and opponent decks**, **trophy levels**, crowns, and related metadata. The pipeline ingests raw data from the official Clash Royale API, normalizes it into a tabular structure, and stores it efficiently in **Parquet**. It also supports **incremental collection** via a visited-clans checkpoint so you can resume from where you left off.

**What you get**
- A reproducible process that outputs a single, tidy **DataFrame of games** (players, opponents, decks, trophies, crowns, etc.) ready for EDA, feature engineering, and modeling.
- **Configurable fields**: the exact attributes pulled from the API can be easily adjusted in code to match your analysis goals.
- **Solid foundation for ML**: the dataset is structured to enable downstream tasks like deck similarity, trophy-range segmentation, win-probability baselines, and more.
- **Production-minded basics**: logging, simple retries/rate-limit handling, Parquet output, and checkpointing for incremental runs.

> In short: this is a flexible, extensible base for deeper analytics and machine learning on Clash Royale data.

---

## 🚀 Quickstart

**1. Clone the repository**
```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set your API token**
```bash
cp .env.example .env
```
Then edit `.env` and set:
```bash
CLASH_API_TOKEN=your_api_token_here
```

**5. Run the main script**
```bash
python main.py
```

---

## ⚙️ Configuration
- **Secret config:** `.env` → `CLASH_API_TOKEN`
- **Public config:** `config.py` → `FIRST_CLAN_TAG`, `MAX_NEW_CLANS`, etc.

---

## 📦 Outputs
- `data/clash_battles.parquet` — main dataset in Parquet format
- `checkpoints/visited_clans.json` — list of already-processed clans for incremental runs

---

## ✨ Features
- Automatic retry & rate-limit handling
- Incremental scraping without revisiting processed clans
- Efficient storage and reload via Parquet format
- Logging for progress tracking and error reporting

---

## 📝 Notes
- Requires a valid Clash Royale API token from [developer.clashroyale.com](https://developer.clashroyale.com)
- This project collects only metadata for analysis; no copyrighted game assets are stored.

---

## 📄 License
MIT License — feel free to use, modify, and share.