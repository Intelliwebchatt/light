   import requests
import json
import yfinance as yf
import feedparser
from datetime import datetime

# --- CONFIGURATION ---
# Fake a browser to stop Google from blocking us
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_stocks():
    tickers = ["^GSPC", "^DJI", "^IXIC", "^VIX"]
    try:
        # Get 5 days to ensure we find a valid trading day
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
    except Exception as e:
        return f"STOCKS ERROR: {str(e)}\n"

def fetch_polymarket():
    text = "TOP 5 BETTING MARKETS (24H Volume)\n"
    try:
        url = "https://gamma-api.polymarket.com/markets?limit=5&active=true&closed=false&order=volume24hr&ascending=false"
        # Polymarket doesn't need headers, but it's safe to include
        r = requests.get(url, headers=HEADERS).json()
        
        for m in r:
            question = m.get('question')
            # FIX: outcomePrices is ALREADY a list, don't use json.loads
            prices = m.get('outcomePrices', [])
            
            if prices and len(prices) > 0:
                # Convert '0.5' string to float
                prob = float(prices[0]) * 100
                text += f"🔵 {question}\n"
                text += f"   YES: {prob:.1f}%\n\n"
    except Exception as e:
        text += f"POLYMARKET ERROR: {str(e)}\n"
    return text

def fetch_news():
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        # Fetch raw XML first with headers
        response = requests.get(url, headers=HEADERS)
        feed = feedparser.parse(response.content)
        
        text = "TOP HEADLINES\n"
        for i, entry in enumerate(feed.entries[:5], 1):
            text += f"• {entry.title}\n"
        return text
    except Exception as e:
        return f"NEWS ERROR: {str(e)}\n"

def fetch_trends():
    try:
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        # Fetch raw XML first with headers to bypass block
        response = requests.get(url, headers=HEADERS)
        feed = feedparser.parse(response.content)
        
        text = "TRENDING SEARCHES\n"
        for i, entry in enumerate(feed.entries[:5], 1):
            text += f"{i}. {entry.title}\n"
        return text
    except Exception as e:
        return f"TRENDS ERROR: {str(e)}\n"

def run():
    date = datetime.utcnow().strftime('%Y-%m-%d')
    report = f"INTELLIGENCE SNAPSHOT // {date}\n"
    report += "="*30 + "\n\n"
    
    report += fetch_stocks() + "\n" + "-"*30 + "\n\n"
    report += fetch_polymarket() + "-"*30 + "\n\n"
    report += fetch_news() + "\n" + "-"*30 + "\n\n"
    report += fetch_trends()
        
    report += "\n="*30 + "\nEND TRANSMISSION"

    with open("daily_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    run()
