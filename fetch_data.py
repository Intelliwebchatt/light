import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# Fake Browser Header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_stocks():
    # Direct API call - No Library Needed
    tickers = {
        "S&P 500": "^GSPC",
        "DOW J": "^DJI",
        "NASDAQ": "^IXIC",
        "VIX": "^VIX"
    }
    output = "MARKET CLOSE\n"
    
    for name, symbol in tickers.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
            data = requests.get(url, headers=HEADERS).json()
            # Dig into the JSON to find the close price
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            output += f"{name}: {price:,.0f}\n"
        except:
            output += f"{name}: --\n"
    return output

def fetch_polymarket_category(tag, label):
    text = f"\n--- {label.upper()} (Top 5 Active) ---\n"
    try:
        url = f"https://gamma-api.polymarket.com/markets?limit=5&active=true&closed=false&order=volume24hr&ascending=false&tag_slug={tag}"
        r = requests.get(url, headers=HEADERS).json()
        
        for m in r:
            question = m.get('question')
            op = m.get('outcomePrices', [])
            # Safety Check: Handle string or list
            if isinstance(op, str): prices = json.loads(op)
            else: prices = op
            
            if prices and len(prices) > 0:
                prob = float(prices[0]) * 100
                text += f"[{prob:.1f}%] {question}\n"
    except:
        text += "No Data.\n"
    return text

def fetch_all_markets():
    report = "PREDICTION MARKETS\n"
    report += fetch_polymarket_category("global-politics", "Geopolitics")
    report += fetch_polymarket_category("politics", "US Politics")
    report += fetch_polymarket_category("technology", "Tech & AI")
    report += fetch_polymarket_category("science", "Science")
    return report

def parse_rss(url, limit=8):
    # Built-in XML parser - No Feedparser needed
    text = ""
    try:
        response = requests.get(url, headers=HEADERS)
        root = ET.fromstring(response.content)
        # Find all <item> tags
        count = 0
        for item in root.findall('.//item'):
            if count >= limit: break
            title = item.find('title').text
            text += f"• {title}\n"
            count += 1
    except:
        text += "• (Feed unavailable)\n"
    return text

def fetch_news():
    return "TOP HEADLINES\n" + parse_rss("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")

def fetch_trends():
    text = "TRENDING TOPICS\n"
    # Try Bing (XML)
    bing_text = parse_rss("https://www.bing.com/news/search?q=trending+stories&format=rss", limit=10)
    
    if "unavailable" not in bing_text:
        text += bing_text
    else:
        # Backup: Yahoo
        text += "(Using Yahoo Backup)\n"
        text += parse_rss("https://news.yahoo.com/rss", limit=10)
    return text

def run():
    date = datetime.utcnow().strftime('%Y-%m-%d')
    report = f"INTELLIGENCE SNAPSHOT // {date}\n"
    report += "="*40 + "\n\n"
    
    report += fetch_stocks() + "\n" + "-"*40 + "\n\n"
    report += fetch_all_markets() + "\n" + "-"*40 + "\n\n"
    report += fetch_news() + "\n" + "-"*40 + "\n\n"
    report += fetch_trends()
        
    report += "\n="*40 + "\nEND TRANSMISSION"

    with open("daily_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    run()
