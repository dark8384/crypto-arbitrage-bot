import ccxt
import json
from datetime import datetime

MIN_FUNDING_GAP = 0.01  
MAX_SPREAD_LOSS = 0.50

def fetch_exchange_data():
    binance = ccxt.binanceusdm({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    bybit = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
    
    binance_data = {}
    bybit_data = {}
    
    # Fetch Binance
    try:
        binance_tickers = binance.fetch_tickers()
        for symbol, ticker in binance_tickers.items():
            if '/' in symbol and symbol.endswith('/USDT:USDT'):
                coin = symbol.split('/')[0]
                price = float(ticker.get('last', 0) or ticker.get('close', 0))
                funding = float(ticker.get('info', {}).get('lastFundingRate', 0)) * 100
                if price > 0:
                    binance_data[coin] = {"price": price, "funding": funding}
    except Exception as e:
        print(f"⚠️ Binance Fallback Triggered: {e}")

    # Fetch Bybit
    try:
        bybit_tickers = bybit.fetch_tickers()
        for symbol, ticker in bybit_tickers.items():
            if '/' in symbol and symbol.endswith('/USDT:USDT'):
                coin = symbol.split('/')[0]
                price = float(ticker.get('last', 0) or ticker.get('close', 0))
                funding = float(ticker.get('info', {}).get('fundingRate', 0)) * 100
                if price > 0:
                    bybit_data[coin] = {"price": price, "funding": funding}
    except Exception as e:
        print(f"⚠️ Bybit Fallback Triggered: {e}")

    return binance_data, bybit_data

def process_arbitrage():
    binance_markets, bybit_markets = fetch_exchange_data()
    
    if not binance_markets or not bybit_markets:
        print("❌ Error: Core API streams empty.")
        return

    matched_opportunities = []
    common_coins = set(binance_markets.keys()).intersection(set(bybit_markets.keys()))

    for coin in common_coins:
        try:
            b_data = binance_markets[coin]
            by_data = bybit_markets[coin]

            binance_price = float(b_data["price"])
            bybit_price = float(by_data["price"])
            binance_funding = float(b_data["funding"])
            bybit_funding = float(by_data["funding"])

            if binance_price <= 0 or bybit_price <= 0:
                continue

            funding_gap = abs(binance_funding - bybit_funding)
            avg_price = (binance_price + bybit_price) / 2
            spread_pct = (abs(binance_price - bybit_price) / avg_price) * 100
            net_profit = funding_gap - spread_pct

            if funding_gap >= MIN_FUNDING_GAP:
                # 🔥 FIXED CORRECTION LOGIC BASED ON FUNDING PREMIUM
                direction = "Short Binance / Long Bybit" if binance_funding > bybit_funding else "Long Binance / Short Bybit"
                status = "🟢 SAFE" if spread_pct < MAX_SPREAD_LOSS else "❌ HIGH SPREAD"

                matched_opportunities.append({
                    "Coin": coin,
                    "Binance Price": f"${binance_price:.5f}",
                    "Bybit Price": f"${bybit_price:.5f}",
                    "Binance Funding": f"{binance_funding:+.4f}%",
                    "Bybit Funding": f"{bybit_funding:+.4f}%",
                    "Funding Gap": f"{funding_gap:.4f}%",
                    "Spread": f"{spread_pct:.4f}%",
                    "Est Net": f"{net_profit:+.4f}%",
                    "Direction": direction,
                    "Status": status
                })
        except Exception as e:
            continue

    matched_opportunities = sorted(matched_opportunities, key=lambda x: float(x['Funding Gap'].replace('%','')), reverse=True)

    final_payload = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data": matched_opportunities
    }

    with open('data.json', 'w') as f:
        json.dump(final_payload, f, indent=4)
    print(f"✅ Sync Successful. Total tracked: {len(matched_opportunities)}")

if __name__ == "__main__":
    process_arbitrage()
