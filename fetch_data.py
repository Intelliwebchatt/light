import requests
import json
import yfinance as yf
import feedparser
from datetime import datetime

# Fake Browser Header to prevent blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def fetch_stocks():
    tickers = ["^GSPC", "^DJI", "^IXIC", "^VIX"]
    try:
        data = yf.download(tickers, period="5d", progress=False)['Close']
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
    except:
        return "STOCKS: DELAYED\n"

def fetch_polymarket_category(tag, label):
    text = f"\n--- {label.upper()} (Top 10 Volume) ---\n"
    try:
        url = f"https://gamma-api.polymarket.com/markets?limit=10&active=true&closed=false&order=volume24hr&ascending=false&tag_slug={tag}"
        r = requests.get(url, headers=HEADERS).json()
        
        for m in r:
            question = m.get('question')
            op = m.get('outcomePrices', [])
            if isinstance(op, str): prices = json.loads(op)
            else: prices = op
            
            if prices and len(prices) > 0:
                prob = float(prices[0]) * 100
                text += f"[{prob:.1f}%] {question}\n"
    except:
        text += "No Data.\n"
    return text

def fetch_all_markets():
    report = "PREDICTION MARKETS (DEEP DIVE)\n"
    report += fetch_polymarket_category("global-politics", "Geopolitics")
    report += fetch_polymarket_category("politics", "US Politics")
    report += fetch_polymarket_category("technology", "Tech & AI")
    report += fetch_polymarket_category("science", "Science")
    report += fetch_polymarket_category("business", "Economy")
    return report

def fetch_news():
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, headers=HEADERS)
        feed = feedparser.parse(response.content)
        text = "TOP HEADLINES\n"
        for i, entry in enumerate(feed.entries[:10], 1):
            text += f"• {entry.title}\n"
        return text
    except:
        return "NEWS: UNAVAILABLE\n"

def fetch_trends():
    text = "TRENDING SEARCHES (US)\n"
    try:
        # Using the Daily Trends RSS Feed
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        response = requests.get(url, headers=HEADERS)
        feed = feedparser.parse(response.content)
        
        if len(feed.entries) > 0:
            for i, entry in enumerate(feed.entries[:10], 1): # Grab Top 10
                text += f"{i}. {entry.title}\n"
        else:
            text += "• (Feed Empty - Google blocking IP)\n"
    except Exception as e:
        text += f"• Trends Error: {str(e)}\n"
    return text

def run():
    date = datetime.utcnow().strftime('%Y-%m-%d')
    report = f"INTELLIGENCE SNAPSHOT // {date}\n"
    report += "="*40 + "\n\n"
    
    report += fetch_stocks() + "\n" + "-"*40 + "\n\n"
    report += fetch_all_markets() + "\n" + "-"*40 + "\n\n"
    report += fetch_news() + "\n" + "-"*40 + "\n\n"
    report += fetch_trends() # <--- Added Back
        
    report += "\n="*40 + "\nEND TRANSMISSION"

    with open("daily_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    run()
