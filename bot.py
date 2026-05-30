import requests
import pandas as pd
import json
from datetime import datetime

# Real-time data filtration boundaries
MIN_FUNDING_GAP = 0.05  
MAX_SPREAD_LOSS = 0.50

def fetch_binance_live():
    # Direct execution endpoint bypassing restrictive region blocks
    url = "https://api1.binance.com/fapi/v1/premiumIndex"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            tickers = {}
            for item in data:
                symbol = item.get('symbol', '')
                if symbol.endswith('USDT'):
                    coin = symbol.replace('USDT', '')
                    tickers[coin] = {
                        "price": float(item.get('markPrice', 0)),
                        "funding": float(item.get('lastFundingRate', 0)) * 100 # Standardizing to %
                    }
            return tickers
    except Exception as e:
        print(f"⚠️ Binance Live Stream Fetch Error: {e}")
    return {}

def fetch_bybit_live():
    # Public alternative global routing cluster checkpoint
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json().get('result', {}).get('list', [])
            tickers = {}
            for item in data:
                symbol = item.get('symbol', '')
                if symbol.endswith('USDT'):
                    coin = symbol.replace('USDT', '')
                    # Bybit serves native orderbook mark prices directly
                    tickers[coin] = {
                        "price": float(item.get('markPrice', 0) or item.get('lastPrice', 0)),
                        "funding": float(item.get('fundingRate', 0)) * 100
                    }
            return tickers
    except Exception as e:
        print(f"⚠️ Bybit Live Stream Fetch Error: {e}")
    return {}

def process_arbitrage():
    print("🔄 Fetching direct global institutional endpoints...")
    binance_markets = fetch_binance_live()
    bybit_markets = fetch_bybit_live()

    if not binance_markets or not bybit_markets:
        print("❌ Error: Core pipelines are empty. Aborting compile sync.")
        return

    matched_opportunities = []
    common_coins = set(binance_markets.keys()).intersection(set(bybit_markets.keys()))

    for coin in common_coins:
        try:
            b_data = binance_markets[coin]
            by_data = bybit_markets[coin]

            b_price = b_data["price"]
            by_price = by_data["price"]
            b_funding = b_data["funding"]
            by_funding = by_data["funding"]

            if b_price <= 0 or by_price <= 0:
                continue

            # Pure mathematical calculations for dynamic matching
            funding_gap = abs(b_funding - by_funding)
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
                    "Binance Funding": f"{b_funding:+.4f}%",
                    "Bybit Funding": f"{by_funding:+.4f}%",
                    "Funding Gap": f"{funding_gap:.4f}%",
                    "Spread": f"{spread_pct:.4f}%",
                    "Est Net": f"{net_profit:+.4f}%",
                    "Direction": direction,
                    "Status": status
                })
        except:
            continue

    # Sorting options highest delta on top
    matched_opportunities = sorted(matched_opportunities, key=lambda x: float(x['Funding Gap'].replace('%','')), reverse=True)

    final_payload = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data": matched_opportunities
    }

    with open('data.json', 'w') as f:
        json.dump(final_payload, f, indent=4)
    print(f"✅ Matrix Synchronized! Total verified assets: {len(matched_opportunities)}")

if __name__ == "__main__":
    process_arbitrage()
