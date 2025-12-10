import requests
import json
import yfinance as yf
import feedparser
from datetime import datetime

# --- CONFIGURATION ---
POLYMARKET_SLUGS = [
    "openai-model-release",
    "israel-lebanon-conflict", 
    "measles-outbreak-usa",
    "spacex-ipo",
    "person-of-the-year-2025"
]

def fetch_stocks():
    # S&P 500, Dow, Nasdaq, VIX
    tickers = ["^GSPC", "^DJI", "^IXIC", "^VIX"]
    data = yf.download(tickers, period="1d", progress=False)['Close']
    
    # Get latest values safely
    sp = f"{data['^GSPC'].iloc[-1]:.0f}"
    dow = f"{data['^DJI'].iloc[-1]:.0f}"
    nas = f"{data['^IXIC'].iloc[-1]:.0f}"
    vix = f"{data['^VIX'].iloc[-1]:.2f}"
    
    return f"""MARKET CLOSE
S&P 500: {sp}
DOW J:   {dow}
NASDAQ:  {nas}
VIX:     {vix}
"""

def fetch_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    feed = feedparser.parse(url)
    text = "TRENDING SEARCHES (US)\n"
    for i, entry in enumerate(feed.entries[:5], 1):
        text += f"{i}. {entry.title}\n"
    return text

def fetch_news():
    url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    text = "TOP HEADLINES\n"
    for i, entry in enumerate(feed.entries[:5], 1):
        text += f"• {entry.title}\n"
    return text

def fetch_polymarket():
    text = "PREDICTION MARKETS\n"
    for slug in POLYMARKET_SLUGS:
        try:
            url = f"https://gamma-api.polymarket.com/events?slug={slug}"
            r = requests.get(url).json()
            if r:
                title = r[0].get('title', slug)
                text += f"🔵 {title.upper()}\n"
                markets = [m for m in r[0].get('markets', []) if not m.get('closed')]
                for m in markets:
                    q = m.get('question')
                    prices = json.loads(m.get('outcomePrices', '[]'))
                    if prices:
                        prob = float(prices[0]) * 100
                        text += f"   {q}: {prob:.1f}%\n"
                text += "\n"
        except:
            continue
    return text

def run():
    date = datetime.utcnow().strftime('%Y-%m-%d')
    report = f"INTELLIGENCE SNAPSHOT // {date}\n"
    report += "="*30 + "\n\n"
    
    try: report += fetch_stocks() + "\n" + "-"*30 + "\n\n"
    except: report += "STOCKS: UNAVAILABLE\n\n"

    try: report += fetch_polymarket() + "-"*30 + "\n\n"
    except: report += "POLYMARKET: UNAVAILABLE\n\n"

    try: report += fetch_news() + "\n" + "-"*30 + "\n\n"
    except: report += "NEWS: UNAVAILABLE\n\n"

    try: report += fetch_trends()
    except: report += "TRENDS: UNAVAILABLE\n"
        
    report += "\n="*30 + "\nEND TRANSMISSION"

    with open("daily_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    run()
