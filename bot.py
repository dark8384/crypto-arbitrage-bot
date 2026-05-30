import ccxt
import json
from datetime import datetime

def fetch_exchange_data():
    # Initializing CCXT instances with modern endpoints
    binance = ccxt.binanceusdm({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    bybit = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
    
    binance_data = {}
    bybit_data = {}
    
    # 1. Fetching Binance Markets safely via CCXT core structures
    try:
        binance_tickers = binance.fetch_tickers()
        for symbol, ticker in binance_tickers.items():
            if '/' in symbol and symbol.endswith('/USDT:USDT'):
                coin = symbol.split('/')[0]
                # Fallback to lastPrice if markPrice parsing shifts
                price = float(ticker.get('info', {}).get('markPrice', 0) or ticker.get('last', 0))
                funding = float(ticker.get('info', {}).get('lastFundingRate', 0)) * 100
                if price > 0:
                    binance_data[coin] = {"price": price, "funding": funding}
    except Exception as e:
        print(f"⚠️ Binance Core API Bypass Triggered: {e}")
        # Secondary fallback layer using direct public aggregator rest stream
        try:
            import requests
            r = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=10).json()
            for item in r:
                sym = item.get('symbol', '')
                if sym.endswith('USDT'):
                    coin = sym.replace('USDT', '')
                    binance_data[coin] = {
                        "price": float(item.get('markPrice', 0)),
                        "funding": float(item.get('lastFundingRate', 0)) * 100
                    }
        except Exception as fallback_err:
            print(f"❌ Critical: Binance fully blocked: {fallback_err}")

    # 2. Fetching Bybit Markets safely
    try:
        bybit_tickers = bybit.fetch_tickers()
        for symbol, ticker in bybit_tickers.items():
            if '/' in symbol and symbol.endswith('/USDT:USDT'):
                coin = symbol.split('/')[0]
                price = float(ticker.get('info', {}).get('markPrice', 0) or ticker.get('last', 0))
                funding = float(ticker.get('info', {}).get('fundingRate', 0)) * 100
                if price > 0:
                    bybit_data[coin] = {"price": price, "funding": funding}
    except Exception as e:
        print(f"⚠️ Bybit Core Parsing Fallback Triggered: {e}")

    return binance_data, bybit_data

def process_matrix():
    b_markets, by_markets = fetch_exchange_data()
    
    if not b_markets or not by_markets:
        print("❌ Pipeline syncing failure: Core structures empty.")
        return

    opportunities = []
    common_coins = set(b_markets.keys()).intersection(set(by_markets.keys()))

    for coin in common_coins:
        b_coin = b_markets[coin]
        by_coin = by_markets[coin]

        # Splitting definitions down to hard floats to break logical 0.0% overwrite bugs
        b_price = float(b_coin["price"])
        by_price = float(by_coin["price"])
        b_funding = float(b_coin["funding"])
        by_funding = float(by_coin["funding"])

        # Safety zero-division anchor filter
        if b_price <= 0 or by_price <= 0:
            continue

        funding_gap = abs(b_funding - by_funding)
        avg_price = (b_price + by_price) / 2.0
        
        # Real-time absolute spread calculation loop
        spread_pct = (abs(b_price - by_price) / avg_price) * 100.0
        net_profit = funding_gap - spread_pct

        direction = "Short Binance / Long Bybit" if b_price > by_price else "Long Binance / Short Bybit"
        status = "🟢 SAFE" if spread_pct < 0.50 else "❌ HIGH SPREAD"

        opportunities.append({
            "Coin": coin,
            "Binance Price": f"${b_price:.6f}",
            "Bybit Price": f"${by_price:.6f}",
            "Binance Funding": f"{b_funding:+.4f}%",
            "Bybit Funding": f"{by_funding:+.4f}%",
            "Funding Gap": f"{funding_gap:.4f}%",
            "Spread": f"{spread_pct:.4f}%",
            "Est Net": f"{net_profit:+.4f}%",
            "Direction": direction,
            "Status": status
        })

    # Sort array based on raw funding premium index
    opportunities = sorted(opportunities, key=lambda x: float(x['Funding Gap'].replace('%','')), reverse=True)

    payload = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data": opportunities
    }

    with open('data.json', 'w') as f:
        json.dump(payload, f, indent=4)
    print(f"✅ Sync complete! Total dynamic synchronized tracking points: {len(opportunities)}")

if __name__ == "__main__":
    process_matrix()
