import ccxt
import pandas as pd
from tabulate import tabulate

# 🌐 FREE PROXY MECHANISM (GitHub ke Blocked IP ko mask karne ke liye)
# Ye proxy server GitHub Actions ke servers ko restricted locations se bypass karwayega
PROXY_URL = 'https://cors-anywhere.herokuapp.com/'

# Bybit setup with proxy bypass
bybit = ccxt.bybit({
    'enableRateLimit': True,
    'headers': {
        'X-Requested-With': 'XMLHttpRequest'
    }
})

# Binance setup with proxy bypass and strict futures endpoint mapping
binance = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future', 
    },
    'headers': {
        'X-Requested-With': 'XMLHttpRequest'
    }
})

# Proxy settings inject kar rahe hain dono exchanges me
binance.proxies = { 'http': PROXY_URL, 'https': PROXY_URL }
bybit.proxies = { 'http': PROXY_URL, 'https': PROXY_URL }

# RISK & PROFIT FILTER RULES
MIN_FUNDING_GAP = 0.20   # Kam se kam 0.20% ka gap hona chahiye
MAX_SPREAD_LOSS = 0.40   # Agar price spread 0.40% se zyada hai toh entry unsafe hai

def scan_markets():
    print("[🔄] GitHub Cloud Server: Proxy Tunnel active. Scanning markets...")
    
    try:
        # Load tickers via proxy tunnel securely
        bybit_tickers = bybit.fetch_tickers()
        binance_tickers = binance.fetch_tickers()
    except Exception as e:
        print(f"❌ Execution Blocked via Proxy: {e}")
        print("Tip: Agar proxy overloaded hai, toh re-run workflow dabayein.")
        return

    opportunities = []
    
    # Extract only valid USDT pairs
    bybit_symbols = {sym for sym in bybit_tickers.keys() if sym.endswith('/USDT')}
    
    for symbol in bybit_symbols:
        try:
            # Map symbol notation variants between Binance and Bybit
            b_symbol = symbol.replace('/USDT', '/USDT:USDT') if '/USDT:USDT' in binance_tickers else symbol
            if b_symbol not in binance_tickers:
                b_symbol = symbol if symbol in binance_tickers else None
                
            if not b_symbol:
                continue

            b_ticker = binance_tickers[b_symbol]
            by_ticker = bybit_tickers[symbol]
            
            b_price = b_ticker['last']
            by_price = by_ticker['last']
            
            if not b_price or not by_price:
                continue
            
            # Extract historical/current funding rates securely
            b_funding = b_ticker['info'].get('lastFundingRate', 0) if 'lastFundingRate' in b_ticker['info'] else 0
            by_funding = by_ticker['info'].get('fundingRate', 0) if 'fundingRate' in by_ticker['info'] else 0

            b_funding_pct = float(b_funding) * 100
            by_funding_pct = float(by_funding) * 100
            
            funding_gap = abs(b_funding_pct - by_funding_pct)
            spread_pct = (abs(b_price - by_price) / ((b_price + by_price) / 2)) * 100
            est_net_profit = funding_gap - spread_pct

            # Filters block validation
            if funding_gap >= MIN_FUNDING_GAP:
                status = "❌ UNSAFE (High Spread)" if spread_pct > MAX_SPREAD_LOSS else "🟢 SAFE TO ENTER"
                direction = "Short Binance / Long Bybit" if b_price > by_price else "Long Binance / Short Bybit"

                opportunities.append({
                    "Coin": symbol.split('/')[0],
                    "Binance Price": f"${b_price:,.4f}",
                    "Bybit Price": f"${by_price:,.4f}",
                    "Binance Funding": f"{b_funding_pct:+.4f}%",
                    "Bybit Funding": f"{by_funding_pct:+.4f}%",
                    "Funding Gap": f"{funding_gap:.4f}%",
                    "Spread": f"{spread_pct:.4f}%",
                    "Est Net": f"{est_net_profit:+.4f}%",
                    "Direction": direction,
                    "Status": status
                })
        except:
            continue

    # Final visual output compile kar rahe hain
    if opportunities:
        df = pd.DataFrame(opportunities).sort_values(by="Funding Gap", ascending=False)
        print("\n" + "="*120)
        print("💰 LIVE CRYPTO ARBITRAGE OPPORTUNITIES (PROXY TUNNELING ACTIVE) 💰")
        print("="*120)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    else:
        print("⚡ Connection Successful! Lekin abhi market me koi coin 0.20% ka gap cross nahi kar raha.")

if __name__ == "__main__":
    scan_markets()
