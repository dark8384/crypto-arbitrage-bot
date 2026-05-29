import requests
import pandas as pd
import json
from datetime import datetime

MIN_FUNDING_GAP = 0.10
MAX_SPREAD_LOSS = 0.35

def fetch_and_generate():
    url = "https://api.coingecko.com/api/v3/derivatives"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return
        data = response.json()
    except:
        return

    opportunities = []

    for item in data:
        try:
            exchange = item.get('market', '').lower()
            if 'binance' not in exchange and 'bybit' not in exchange:
                continue

            symbol = item.get('symbol', '')
            if not symbol.endswith('USDT'):
                continue

            coin = symbol.replace('USDT', '')
            price = float(item.get('price', 0))
            funding_rate = float(item.get('funding_rate', 0))
            
            if price <= 0:
                continue

            opportunities.append({
                "Coin": coin,
                "Exchange": "Binance" if "binance" in exchange else "Bybit",
                "Price": price,
                "Funding Rate": funding_rate
            })
        except:
            continue

    if not opportunities:
        return

    df_raw = pd.DataFrame(opportunities)
    binance_df = df_raw[df_raw['Exchange'] == 'Binance'].set_index('Coin')
    bybit_df = df_raw[df_raw['Exchange'] == 'Bybit'].set_index('Coin')

    matched_opportunities = []
    common_coins = set(binance_df.index).intersection(set(bybit_df.index))

    for coin in common_coins:
        try:
            b_rate = binance_df.loc[coin, 'Funding Rate']
            by_rate = bybit_df.loc[coin, 'Funding Rate']
            if isinstance(b_rate, pd.Series): b_rate = b_rate.iloc[0]
            if isinstance(by_rate, pd.Series): by_rate = by_rate.iloc[0]
            
            b_price = binance_df.loc[coin, 'Price']
            by_price = bybit_df.loc[coin, 'Price']
            if isinstance(b_price, pd.Series): b_price = b_price.iloc[0]
            if isinstance(by_price, pd.Series): by_price = by_price.iloc[0]

            if b_price <= 0 or by_price <= 0:
                continue

            funding_gap = abs(b_rate - by_rate)
            avg_price = (b_price + by_price) / 2
            spread_pct = (abs(b_price - by_price) / avg_price) * 100
            net_profit = funding_gap - spread_pct

            if funding_gap >= MIN_FUNDING_GAP:
                direction = "Short Binance / Long Bybit" if b_price > by_price else "Long Binance / Short Bybit"
                status = "🟢 SAFE" if spread_pct < MAX_SPREAD_LOSS else "❌ HIGH SPREAD"

                matched_opportunities.append({
                    "Coin": coin,
                    "Binance Price": f"${b_price:,.4f}",
                    "Bybit Price": f"${by_price:,.4f}",
                    "Binance Funding": f"{b_rate:+.4f}%",
                    "Bybit Funding": f"{by_rate:+.4f}%",
                    "Funding Gap": f"{funding_gap:.4f}%",
                    "Spread": f"{spread_pct:.4f}%",
                    "Est Net": f"{net_profit:+.4f}%",
                    "Direction": direction,
                    "Status": status
                })
        except:
            continue

    # JSON formats me save kar rahe hain taaki webpage ise fetch karke refresh kar sake
    final_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data": matched_opportunities if matched_opportunities else []
    }
    
    with open('data.json', 'w') as f:
        json.dump(final_data, f, indent=4)
    print("✅ data.json file successfully updated for dashboard.")

if __name__ == "__main__":
    fetch_and_generate()
