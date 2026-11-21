import os
import time
from datetime import datetime, timezone
import pandas as pd
import requests

DATA_PATH = "data/crypto_market_daily.csv"

# لائحة عملات رئيسية (تقدر تزيد أو تنقص حسب الرغبة)
COINS = [
    ("bitcoin", "BTC", "Bitcoin", 1),
    ("ethereum", "ETH", "Ethereum", 2),
    ("tether", "USDT", "Tether", 3),
    ("binancecoin", "BNB", "BNB", 4),
    ("solana", "SOL", "Solana", 5),
    ("ripple", "XRP", "XRP", 6),
    ("usd-coin", "USDC", "USDC", 7),
    ("cardano", "ADA", "Cardano", 8),
    ("dogecoin", "DOGE", "Dogecoin", 9),
    ("avalanche-2", "AVAX", "Avalanche", 10),
    ("polkadot", "DOT", "Polkadot", 11),
    ("chainlink", "LINK", "Chainlink", 12),
    ("tron", "TRX", "TRON", 13),
    ("litecoin", "LTC", "Litecoin", 14),
    ("uniswap", "UNI", "Uniswap", 15),
]

def fetch_coin_history(coin_id: str, days: int = 365):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": str(days),
        "interval": "daily",
    }
    headers = {"User-Agent": "Mozilla/5.0 (KaggleCryptoDatasetBot/1.0)"}
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def build_history(days: int = 365):
    all_rows = []

    for coin_id, symbol, name, base_rank in COINS:
        print(f"Fetching {days}d history for {name} ({symbol})...")
        try:
            data = fetch_coin_history(coin_id, days=days)
        except Exception as e:
            print(f"Error fetching {coin_id}: {e}")
            time.sleep(5)
            continue

        prices = {
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d"): val
            for ts, val in data.get("prices", [])
        }
        market_caps = {
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d"): val
            for ts, val in data.get("market_caps", [])
        }
        volumes = {
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d"): val
            for ts, val in data.get("total_volumes", [])
        }

        dates = sorted(prices.keys())
        for i, d in enumerate(dates):
            p = prices.get(d)
            prev_24h_p = prices.get(dates[i - 1]) if i > 0 else None
            prev_7d_p = prices.get(dates[i - 7]) if i >= 7 else None

            chg_24h = ((p - prev_24h_p) / prev_24h_p * 100) if (p and prev_24h_p) else None
            chg_7d = ((p - prev_7d_p) / prev_7d_p * 100) if (p and prev_7d_p) else None

            all_rows.append({
                "snapshot_date": d,
                "snapshot_timestamp_utc": f"{d} 00:00:00",
                "rank": base_rank,
                "coin_id": coin_id,
                "symbol": symbol,
                "name": name,
                "price_usd": p,
                "market_cap_usd": market_caps.get(d),
                "volume_24h_usd": volumes.get(d),
                "high_24h_usd": None,
                "low_24h_usd": None,
                "price_change_1h_pct": None,
                "price_change_24h_pct": round(chg_24h, 4) if chg_24h is not None else None,
                "price_change_7d_pct": round(chg_7d, 4) if chg_7d is not None else None,
                "circulating_supply": None,
                "total_supply": None,
                "ath_usd": None,
                "ath_change_pct": None,
            })

        # احترام Rate Limit ديال الخطة المجانية لـ CoinGecko
        time.sleep(2.5)

    df = pd.DataFrame(all_rows)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    if os.path.exists(DATA_PATH):
        old_df = pd.read_csv(DATA_PATH)
        df = pd.concat([df, old_df], ignore_index=True)
        df.drop_duplicates(subset=["snapshot_date", "coin_id"], keep="last", inplace=True)

    df.sort_values(by=["snapshot_date", "rank"], ascending=[False, True], inplace=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"Done! Saved {len(df)} historical rows to {DATA_PATH}")

if __name__ == "__main__":
    build_history(days=365)
