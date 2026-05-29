import ccxt
import pandas as pd
from tabulate import tabulate

# Exchanges initialize kar rahe hain
binance = ccxt.binance({'enableRateLimit': True})
bybit = ccxt.bybit({'enableRateLimit': True})

# Filters for Safety
MIN_FUNDING_GAP = 0.20   # Kam se kam 0.20% ka gap hona chahiye
MAX_SPREAD_LOSS = 0.40   # Agar price gap 0.40% se zyada hai toh entry risky hai

def scan_markets():
    print("[🔄] GitHub Cloud Server par scanning shuru ho gayi hai...")
    try:
        binance_tickers = binance.fetch_tickers()
        bybit_tickers = bybit.fetch_tickers()
    except Exception as e:
        print(f"❌ Market data fetch karne me error aaya: {e}")
        return

    opportunities = []
    
    # Dono exchanges ke common USDT pairs check karna
    common_symbols = set(binance_tickers.keys()).intersection(set(bybit_tickers.keys()))
    usdt_pairs = [sym for sym in common_symbols if sym.endswith('/USDT')]

    for symbol in usdt_pairs:
        try:
            b_ticker = binance_tickers[symbol]
            by_ticker = bybit_tickers[symbol]
            
            b_price = b_ticker['last']
            by_price = by_ticker['last']
            
            if not b_price or not by_price:
                continue
            
            # Funding Rates read karna
            b_funding = b_ticker['info'].get('lastFundingRate', 0) if 'lastFundingRate' in b_ticker['info'] else 0
            by_funding = by_ticker['info'].get('fundingRate', 0) if 'fundingRate' in by_ticker['info'] else 0

            b_funding_pct = float(b_funding) * 100
            by_funding_pct = float(by_funding) * 100
            
            # Funding Difference
            funding_gap = abs(b_funding_pct - by_funding_pct)

            # Order Book Spread (Price Diff)
            price_diff = abs(b_price - by_price)
            mid_price = (b_price + by_price) / 2
            spread_pct = (price_diff / mid_price) * 100
            
            # Net estimated return
            est_net_profit = funding_gap - spread_pct

            # Sirf badi opportunities filter karna
            if funding_gap >= MIN_FUNDING_GAP:
                if spread_pct > MAX_SPREAD_LOSS:
                    status = "❌ UNSAFE (High Spread)"
                else:
                    status = "🟢 SAFE TO ENTER"
                    
                if b_price > by_price:
                    direction = "Short Binance / Long Bybit"
                else:
                    direction = "Long Binance / Short Bybit"

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

    # Output Table Print karna
    if opportunities:
        df = pd.DataFrame(opportunities).sort_values(by="Funding Gap", ascending=False)
        print("\n" + "="*120)
        print("💰 LIVE CRYPTO ARBITRAGE OPPORTUNITIES 💰")
        print("="*120)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    else:
        print("⚡ Is time market me koi bada funding gap nahi chal raha hai.")

if __name__ == "__main__":
    scan_markets()
