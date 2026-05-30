import requests
import pandas as pd
import json
from datetime import datetime

MIN_FUNDING_GAP = 0.01  # Thoda kam kiya taaki saare live assets pakad me aayein
MAX_SPREAD_LOSS = 3.5   # 3.5% tak ke massive layout allow karenge scanning me

def fetch_and_generate():
    opportunities = []
    
    # 1. Fetch Real-time Binance Premium Index (Prices + Live Funding)
    # GITHUB CLOUD SERVER RESTRICTION BYPASS: Using alternative official api3 cluster endpoint
    binance_url = "https://api3.binance.com/fapi/v1/premiumIndex"
    try:
        b_res = requests.get(binance_url, timeout=10).json()
        binance_data = {item['symbol']: item for item in b_res if item['symbol'].endswith('USDT')}
    except Exception as e:
        print(f"❌ Binance Endpoint Error: {e}")
        binance_data = {}

    # 2. Fetch Real-time Bybit Tickers (Live Last Price + Funding)
    # GITHUB CLOUD SERVER RESTRICTION BYPASS: Using global structural network gateway endpoint
    bybit_url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        by_res = requests.get(bybit_url, timeout=10).json()
        bybit_list = by_res.get('result', {}).get('list', [])
        bybit_data = {item['symbol']: item for item in bybit_list if item['symbol'].endswith('USDT')}
    except Exception as e:
        print(f"❌ Bybit Endpoint Error: {e}")
        bybit_data = {}

    # 3. Structural Cross-Matching Live Matrix
    common_symbols = set(binance_data.keys()).intersection(set(bybit_data.keys()))

    for symbol in common_symbols:
        try:
            b_item = binance_data[symbol]
            by_item = bybit_data[symbol]

            coin = symbol.replace('USDT', '')
            
            # Strict Extract Live Prices
            b_price = float(b_item.get('markPrice', 0))
            by_price = float(by_item.get('lastPrice', 0))
            if b_price <= 0 or by_price <= 0:
                continue

            # Strict Extract Live Funding Rates (Convert directly to percentage format)
            b_rate = float(b_item.get('lastFundingRate', 0)) * 100
            by_rate = float(by_item.get('fundingRate', 0)) * 100

            # Mathematical Formula Updates
            funding_gap = abs(b_rate - by_rate)
            avg_price = (b_price + by_price) / 2
            
            # Calculating raw mathematical divergence between orderbooks
            spread_pct = (abs(b_price - by_price) / avg_price) * 100
            net_profit = funding_gap - spread_pct

            if funding_gap >= MIN_FUNDING_GAP:
                direction = "Short Binance / Long Bybit" if b_price > by_price else "Long Binance / Short Bybit"
                status = "🟢 SAFE" if spread_pct < MAX_SPREAD_LOSS else "❌ HIGH SPREAD"

                opportunities.append({
                    "Coin": coin,
                    "Binance Price": f"${b_price:,.4f}",
                    "Bybit Price": f"${by_price:,.4f}",
                    "Binance Funding": f"{b_rate:+.4f}%",
                    "Bybit Funding": f"{by_rate:+.4f}%",
                    "Funding Gap": f"{funding_gap:.4f}%",
                    "Spread": f"{spread_pct:.4f}%",
                    "Est Net": f"{net_profit:+.4f}%",
                    "Direction": direction,
                    "Status": status,
                    "raw_gap": funding_gap
                })
        except:
            continue

    if not opportunities:
        print("⚠️ No assets passed standard verification criteria right now.")
        return

    # Sort opportunities by highest funding gap dynamically
    opportunities = sorted(opportunities, key=lambda x: x['raw_gap'], reverse=True)
    for op in opportunities:
        op.pop('raw_gap', None) # UI framework injection cleanup

    final_data = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data": opportunities
    }
    
    with open('data.json', 'w') as f:
        json.dump(final_data, f, indent=4)
    print(f"✅ Target compilation done. Synced {len(opportunities)} tickers in real-time.")

if __name__ == "__main__":
    fetch_and_generate()
