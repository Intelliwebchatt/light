import requests
import json
from datetime import datetime

# WATCHLIST: Add the URL "slugs" here
WATCHLIST = [
    "openai-model-release",
    "israel-lebanon-conflict", 
    "measles-outbreak-usa",
    "spacex-ipo",
    "person-of-the-year-2025"
]

def get_data():
    # Header
    text = f"INTELLIGENCE SNAPSHOT\nDATE: {datetime.utcnow().strftime('%Y-%m-%d')}\n"
    text += "="*25 + "\n\n"

    for slug in WATCHLIST:
        try:
            url = f"https://gamma-api.polymarket.com/events?slug={slug}"
            r = requests.get(url).json()
            
            if r:
                title = r[0].get('title', slug)
                text += f"🔵 {title.upper()}\n"
                
                # Filter active markets
                markets = [m for m in r[0].get('markets', []) if not m.get('closed')]
                
                for m in markets:
                    q = m.get('question')
                    # Get 'Yes' price
                    prices = json.loads(m.get('outcomePrices', '[]'))
                    if prices:
                        prob = float(prices[0]) * 100
                        text += f"   > {q}\n"
                        text += f"     ODDS: {prob:.1f}%\n"
                text += "\n"
        except:
            continue

    text += "="*25 + "\nEND OF LINE."
    
    with open("daily_report.txt", "w") as f:
        f.write(text)

if __name__ == "__main__":
    get_data()
