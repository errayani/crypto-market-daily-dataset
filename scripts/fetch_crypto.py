import os
from datetime import datetime, timezone
import pandas as pd
import requests

DATA_PATH = "data/crypto_market_daily.csv"
URL = "https://api.coingecko.com/api/v3/coins/markets"

PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 100,
    "page": 1,
    "sparkline": "false",
    "price_change_percentage": "1h,24h,7d",
}

def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (KaggleCryptoDatasetBot/1.0)"}
    response = requests.get(URL, params=PARAMS, headers=headers, timeout=30)
    response.raise_for_status()
    raw = response.json()

    now_utc = datetime.now(timezone.utc)
    snapshot_date = now_utc.strftime("%Y-%m-%d")
    snapshot_ts = now_utc.strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for coin in raw:
        rows.append({
            "snapshot_date": snapshot_date,
            "snapshot_timestamp_utc": snapshot_ts,
            "rank": coin.get("market_cap_rank"),
            "coin_id": coin.get("id"),
            "symbol": coin.get("symbol", "").upper(),
            "name": coin.get("name"),
            "price_usd": coin.get("current_price"),
            "market_cap_usd": coin.get("market_cap"),
            "volume_24h_usd": coin.get("total_volume"),
            "high_24h_usd": coin.get("high_24h"),
            "low_24h_usd": coin.get("low_24h"),
            "price_change_1h_pct": coin.get("price_change_percentage_1h_in_currency"),
            "price_change_24h_pct": coin.get("price_change_percentage_24h_in_currency"),
            "price_change_7d_pct": coin.get("price_change_percentage_7d_in_currency"),
            "circulating_supply": coin.get("circulating_supply"),
            "total_supply": coin.get("total_supply"),
            "ath_usd": coin.get("ath"),
            "ath_change_pct": coin.get("ath_change_percentage"),
        })

    new_df = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if os.path.exists(DATA_PATH):
        old_df = pd.read_csv(DATA_PATH)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        # منع التكرار إذا اشتغل السكريبت مرتين في نفس اليوم لنفس العملة
        combined.drop_duplicates(subset=["snapshot_date", "coin_id"], keep="last", inplace=True)
    else:
        combined = new_df

    combined.sort_values(by=["snapshot_date", "rank"], ascending=[False, True], inplace=True)
    combined.to_csv(DATA_PATH, index=False)
    print(f"Saved {len(combined)} total rows. Latest snapshot: {snapshot_date}")

if __name__ == "__main__":
    fetch_data()
