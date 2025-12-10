import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Fake Browser Header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# -------------------------------
# STOCKS
# -------------------------------

def fetch_stocks():
    tickers = {
        "S&P 500": "^GSPC",
        "DOW J": "^DJI",
        "NASDAQ": "^IXIC",
        "VIX": "^VIX"
    }
    output = "MARKET CLOSE\n"
    data_block = {}

    for name, symbol in tickers.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
            resp = requests.get(url, headers=HEADERS).json()
            price = resp["chart"]["result"][0]["meta"]["regularMarketPrice"]
            output += f"{name}: {price:,.0f}\n"
            data_block[name] = price
        except Exception:
            output += f"{name}: --\n"
            data_block[name] = None

    return output, data_block

# -------------------------------
# POLYMARKET
# -------------------------------

def normalize_polymarket_market(m, category_label):
    """
    Take one Polymarket market object and extract useful fields.
    This is defensive: keys may or may not exist; we do not assume.
    """
    question = m.get("question")
    market_id = m.get("slug") or m.get("id") or m.get("conditionId")

    # outcomePrices can be list or JSON string
    op = m.get("outcomePrices", [])
    if isinstance(op, str):
        try:
            prices = json.loads(op)
        except Exception:
            prices = []
    else:
        prices = op or []

    probability = None
    if prices:
        try:
            probability = float(prices[0]) * 100.0
        except Exception:
            probability = None

    volume_24h = m.get("volume24hr") or m.get("volume24Hour") or None
    tags = m.get("tags") or m.get("tagSlugs") or []

    # Try to capture some kind of end date if the API provides it
    end_date_raw = m.get("endDate") or m.get("closeTime") or m.get("endTime")
    created_at_raw = m.get("createdAt") or m.get("created")

    end_date = end_date_raw
    created_at = created_at_raw

    # Compute days_to_deadline if possible (rough)
    days_to_deadline = None
    if end_date_raw:
        try:
            # Many APIs use ISO format; this will fail gracefully otherwise
            dt_end = datetime.fromisoformat(end_date_raw.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            delta = dt_end - now_utc
            days_to_deadline = delta.total_seconds() / 86400.0
        except Exception:
            days_to_deadline = None

    market_obj = {
        "market_id": market_id,
        "question": question,
        "category_label": category_label,
        "category_raw": m.get("category"),
        "primary_outcome": "Yes",  # your use-case tracks Yes side
        "probability": probability,  # float percent, may be None
        "volume_24h": volume_24h,
        "tags": tags,
        "end_date": end_date,
        "created_at": created_at,
        "days_to_deadline": days_to_deadline
        # Note: 24h change would need another API or stored prior snapshot
    }

    return market_obj

def fetch_polymarket_category_json(tag, label):
    """
    Returns:
      text_block: pretty text lines for your human report
      markets_list: list of normalized market dicts for JSON feed
    """
    text = f"\n--- {label.upper()} (Top 5 Active) ---\n"
    markets_list = []

    try:
        url = (
            "https://gamma-api.polymarket.com/markets"
            "?limit=5&active=true&closed=false"
            "&order=volume24hr&ascending=false"
            f"&tag_slug={tag}"
        )
        r = requests.get(url, headers=HEADERS).json()

        # Polymarket returns either a list or an object with a list; be defensive
        if isinstance(r, dict) and "markets" in r:
            markets = r["markets"]
        else:
            markets = r

        for m in markets:
            # Build text line
            question = m.get("question")
            op = m.get("outcomePrices", [])
            if isinstance(op, str):
                try:
                    prices = json.loads(op)
                except Exception:
                    prices = []
            else:
                prices = op or []

            prob = None
            if prices:
                try:
                    prob = float(prices[0]) * 100.0
                except Exception:
                    prob = None

            if prob is not None and question:
                text += f"[{prob:.1f}%] {question}\n"
            elif question:
                text += f"[--] {question}\n"

            # Build structured record
            markets_list.append(normalize_polymarket_market(m, label))
    except Exception:
        text += "No Data.\n"

    return text, markets_list

def fetch_all_markets():
    """
    Returns:
      report_text: human-readable block
      markets_data: list of market dicts across categories
    """
    report = "PREDICTION MARKETS\n"
    markets_data = []

    category_specs = [
        ("global-politics", "Geopolitics"),
        ("politics", "US Politics"),
        ("technology", "Tech & AI"),
        ("science", "Science"),
    ]

    seen_ids = set()

    for tag, label in category_specs:
        text_block, markets_list = fetch_polymarket_category_json(tag, label)
        report += text_block

        # Optional: avoid duplicates across categories
        for m in markets_list:
            mid = m.get("market_id")
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            markets_data.append(m)

    return report, markets_data

# -------------------------------
# RSS / NEWS
# -------------------------------

def parse_rss(url, limit=8):
    text = ""
    titles = []
    try:
        response = requests.get(url, headers=HEADERS)
        root = ET.fromstring(response.content)
        count = 0
        for item in root.findall(".//item"):
            if count >= limit:
                break
            title_node = item.find("title")
            if title_node is not None and title_node.text:
                title = title_node.text
                text += f"• {title}\n"
                titles.append(title)
                count += 1
    except Exception:
        text += "• (Feed unavailable)\n"
    return text, titles

def fetch_news():
    header = "TOP HEADLINES\n"
    text_block, titles = parse_rss(
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    )
    return header + text_block, titles

def fetch_trends():
    text = "TRENDING TOPICS\n"
    topics = []

    bing_text, bing_titles = parse_rss(
        "https://www.bing.com/news/search?q=trending+stories&format=rss",
        limit=10,
    )

    if "unavailable" not in bing_text:
        text += bing_text
        topics.extend(bing_titles)
    else:
        text += "(Using Yahoo Backup)\n"
        yahoo_text, yahoo_titles = parse_rss("https://news.yahoo.com/rss", limit=10)
        text += yahoo_text
        topics.extend(yahoo_titles)

    return text, topics

# -------------------------------
# MAIN
# -------------------------------

def run():
    date_utc = datetime.utcnow().strftime("%Y-%m-%d")
    report = f"INTELLIGENCE SNAPSHOT // {date_utc}\n"
    report += "=" * 40 + "\n\n"

    # Stocks
    stocks_text, stocks_data = fetch_stocks()
    report += stocks_text + "\n" + "-" * 40 + "\n\n"

    # Polymarket
    markets_text, markets_data = fetch_all_markets()
    report += markets_text + "\n" + "-" * 40 + "\n\n"

    # News
    news_text, news_titles = fetch_news()
    report += news_text + "\n" + "-" * 40 + "\n\n"

    # Trends
    trends_text, trend_titles = fetch_trends()
    report += trends_text

    report += "\n" + "=" * 40 + "\nEND TRANSMISSION"

    # Write human-readable text
    with open("daily_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    # Build structured JSON for AI consumption
    structured = {
        "snapshot_source": "intelligence_snapshot_script",
        "snapshot_captured_at_utc": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "market_close": stocks_data,
        "polymarket_markets": markets_data,
        "top_headlines": news_titles,
        "trending_topics": trend_titles,
    }

    with open("daily_report.json", "w", encoding="utf-8") as jf:
        json.dump(structured, jf, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
