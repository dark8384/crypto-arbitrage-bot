import requests
import json
from datetime import datetime

MIN_FUNDING_GAP = 0.01  # Sabhi active pairs dekhne ke liye threshold low rakha hai
MAX_SPREAD_LOSS = 0.50

def fetch_binance_live():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            tickers = {}
            for item in res.json():
                symbol = item.get('symbol', '')
                if symbol.endswith('USDT'):
                    coin = symbol.replace('USDT', '')
                    tickers[coin] = {
                        "price": float(item.get('markPrice', 0)),
                        "funding": float(item.get('lastFundingRate', 0)) * 100
                    }
            return tickers
    except Exception as e:
        print(f"⚠️ Binance Direct Fetch Error: {e}")
    return {}

def fetch_bybit_live():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            tickers = {}
            for item in res.json().get('result', {}).get('list', []):
                symbol = item.get('symbol', '')
                if symbol.endswith('USDT'):
                    coin = symbol.replace('USDT', '')
                    tickers[coin] = {
                        "price": float(item.get('markPrice', 0) or item.get('lastPrice', 0)),
                        "funding": float(item.get('fundingRate', 0)) * 100
                    }
            return tickers
    except Exception as e:
        print(f"⚠️ Bybit Direct Fetch Error: {e}")
    return {}

def process_arbitrage():
    print("🔄 Fetching Live Data from Binance and Bybit...")
    binance_markets = fetch_binance_live()
    bybit_markets = fetch_bybit_live()

    if not binance_markets or not bybit_markets:
        print("❌ Data pipelines are empty! Aborting.")
        return

    matched_opportunities = []
    common_coins = set(binance_markets.keys()).intersection(set(bybit_markets.keys()))

    for coin in common_coins:
        b_data = binance_markets[coin]
        by_data = bybit_markets[coin]

        # FIX: Explicitly extraction of separate individual values
        b_price = float(b_data["price"])
        by_price = float(by_data["price"])
        b_funding = float(b_data["funding"])
        by_funding = float(by_data["funding"])

        if b_price <= 0 or by_price <= 0:
            continue

        funding_gap = abs(b_funding - by_funding)
        avg_price = (b_price + by_price) / 2
        
        # Real-time Spread Delta Calculation Fixed
        spread_pct = (abs(b_price - by_price) / avg_price) * 100
        net_profit = funding_gap - spread_pct

        if funding_gap >= MIN_FUNDING_GAP:
            direction = "Short Binance / Long Bybit" if b_price > by_price else "Long Binance / Short Bybit"
            status = "🟢 SAFE" if spread_pct < MAX_SPREAD_LOSS else "❌ HIGH SPREAD"

            matched_opportunities.append({
                "Coin": coin,
                "Binance Price": f"${b_price:.5f}",
                "Bybit Price": f"${by_price:.5f}",
                "Binance Funding": f"{b_funding:+.4f}%",
                "Bybit Funding": f"{by_funding:+.4f}%",
                "Funding Gap": f"{funding_gap:.4f}%",
                "Spread": f"{spread_pct:.4f}%",
                "Est Net": f"{net_profit:+.4f}%",
                "Direction": direction,
                "Status": status
            })

    # Sorting based on highest gap
    matched_opportunities = sorted(matched_opportunities, key=lambda x: float(x['Funding Gap'].replace('%','')), reverse=True)

    final_payload = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data": matched_opportunities
    }

    with open('data.json', 'w') as f:
        json.dump(final_payload, f, indent=4)
    print(f"✅ Matrix Updated Successfully! Total Pairs: {len(matched_opportunities)}")

if __name__ == "__main__":
    process_arbitrage()
