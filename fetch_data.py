import requests
import json
import yfinance as yf
import feedparser
import time
from datetime import datetime

# Fake Browser Header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
    text = f"\n--- {label.upper()} (Top 10 by Volume) ---\n"
    try:
        # Grab top 10 active markets for this category
        url = f"https://gamma-api.polymarket.com/markets?limit=10&active=true&closed=false&order=volume24hr&ascending=false&tag_slug={tag}"
        r = requests.get(url, headers=HEADERS).json()
        
        for m in r:
            question = m.get('question')
            op = m.get('outcomePrices', [])
            
            # Safety Check on Prices
            if isinstance(op, str): prices = json.loads(op)
            else: prices = op
            
            if prices and len(prices) > 0:
                prob = float(prices[0]) * 100
                text += f"[{prob:.1f}%] {question}\n"
    except:
        text += "No Data.\n"
    return text

def fetch_all_markets():
    # The "Vacuum": Pulls data from every major sector
    report = "PREDICTION MARKETS (DEEP DIVE)\n"
    
    # 1. Global Conflict & Politics
    report += fetch_polymarket_category("global-politics", "Geopolitics")
    
    # 2. US Politics
    report += fetch_polymarket_category("politics", "US Politics")
    
    # 3. Technology & AI
    report += fetch_polymarket_category("technology", "Tech & AI")
    
    # 4. Science (includes Space/Health)
    report += fetch_polymarket_category("science", "Science")
    
    # 5. Business/Economy
    report += fetch_polymarket_category("business", "Economy")
    
    return report

def fetch_news():
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, headers=HEADERS)
        feed = feedparser.parse(response.content)
        text = "TOP HEADLINES\n"
        for i, entry in enumerate(feed.entries[:10], 1): # Grab Top 10
            text += f"• {entry.title}\n"
        return text
    except:
        return "NEWS: UNAVAILABLE\n"

def run():
    date = datetime.utcnow().strftime('%Y-%m-%d')
    report = f"INTELLIGENCE SNAPSHOT // {date}\n"
    report += "="*40 + "\n\n"
    
    report += fetch_stocks() + "\n" + "-"*40 + "\n\n"
    report += fetch_all_markets() + "\n" + "-"*40 + "\n\n"
    report += fetch_news()
        
    report += "\n="*40 + "\nEND TRANSMISSION"

    with open("daily_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    run()
