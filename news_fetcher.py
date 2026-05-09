"""
news_fetcher.py
Fetches latest defence & geopolitics news using FREE sources:
1. GDELT Project API (Last 24h filter)
2. Google News RSS (Last 24h filter)
3. NewsAPI.org (Free tier)
4. Reddit (Trending defence posts)
"""

import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

log = logging.getLogger(__name__)

# ── SEARCH QUERIES ─────────────────────────────────────────────
# Updated for 2026 recency to avoid 2024 historical archives
DEFENCE_QUERIES = [
    "India defence military news latest",
    "Indian Army Navy Air Force 2026",
    "India Pakistan border update today",
    "India China LAC border news",
    "DRDO missile test latest",
    "India geopolitics strategic analysis",
    "Indo Pacific QUAD news 2026",
    "Indian Ocean naval security",
    "India defence manufacturing update",
    "Ministry of Defence India press release",
]

# ── SOURCE 1: GDELT PROJECT ────────────────────────────────────
GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"

def fetch_gdelt_news(max_results: int = 20) -> list:
    """
    Fetch defence/geopolitics news from GDELT Project
    GDELT monitors every major news source on the internet
    """
    articles = []
    for query in DEFENCE_QUERIES[:5]:
        try:
            params = {
                'query':      f'{query} sourcelang:english',
                'mode':       'artlist',
                'maxrecords': '10',
                'format':     'json',
                'sort':       'date',
                'timespan':   '1d',  # STRICTLY last 24 hours
            }

            response = requests.get(GDELT_API, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                items = data.get('articles', [])
                log.info(f"GDELT '{query}' → {len(items)} articles")

                for item in items:
                    title = item.get('title', '').strip()
                    if title and len(title) > 20:
                        articles.append({
                            'title': title,
                            'description': title,
                            'url': item.get('url', ''),
                            'source': item.get('domain', ''),
                            'published': item.get('seendate', ''),
                            'origin': 'GDELT',
                            'keywords': query.split(),
                        })
        except Exception as e:
            log.error(f"GDELT error for '{query}': {e}")
    return articles

# ── SOURCE 2: GOOGLE NEWS RSS ──────────────────────────────────
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

def fetch_google_news_rss(max_results: int = 30) -> list:
    """
    Fetch news from Google News RSS feeds
    Optimized for 2026 recency
    """
    articles = []
    for query in DEFENCE_QUERIES[:8]:
        try:
            # THE FIX: 'when:1d' forces results from the last 24 hours only
            time_filtered_query = f"{query} when:1d"
            url = f"{GOOGLE_NEWS_RSS}?q={quote(time_filtered_query)}&hl=en-IN&gl=IN&ceid=IN:en"

            response = requests.get(
                url, 
                timeout=15, 
                headers={'User-Agent': 'Mozilla/5.0 (compatible; DefencePostBot/1.0)'}
            )

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                channel = root.find('channel')
                if channel is None: continue

                items = channel.findall('item')
                log.info(f"Google News '{query}' → {len(items)} articles found")

                for item in items[:5]:
                    pub_el = item.find('pubDate')
                    pub_date_str = pub_el.text if pub_el is not None else ''
                    
                    # EXTRA SAFETY: Skip if the year is 2024 or 2025
                    if any(year in pub_date_str for year in ["2024", "2025"]):
                        continue 

                    title_el = item.find('title')
                    link_el = item.find('link')
                    source_el = item.find('source')

                    title = title_el.text if title_el is not None else ''
                    if title and ' - ' in title:
                        title = title.rsplit(' - ', 1)[0].strip()

                    if title and len(title) > 20:
                        articles.append({
                            'title': title,
                            'description': title,
                            'url': link_el.text if link_el is not None else '',
                            'source': source_el.text if source_el is not None else 'Google News',
                            'published': pub_date_str,
                            'origin': 'Google News',
                            'keywords': query.split(),
                        })
        except Exception as e:
            log.error(f"Google News error for '{query}': {e}")
    return articles

# ── SOURCE 3: NEWSAPI.ORG ──────────────────────────────────────
NEWSAPI_URL = "https://newsapi.org/v2/everything"

def fetch_newsapi(api_key: str, max_results: int = 20) -> list:
    if not api_key: return []
    articles = []
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    queries = ["India defence", "India military", "DRDO latest"]
    for query in queries:
        try:
            params = {
                'q': query,
                'from': yesterday,
                'sortBy': 'publishedAt',
                'apiKey': api_key,
                'language': 'en',
                'pageSize': '10'
            }
            response = requests.get(NEWSAPI_URL, params=params, timeout=15)
            if response.status_code == 200:
                items = response.json().get('articles', [])
                for item in items:
                    articles.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', {}).get('name', 'NewsAPI'),
                        'published': item.get('publishedAt', ''),
                        'origin': 'NewsAPI',
                    })
        except Exception as e:
            log.error(f"NewsAPI error: {e}")
    return articles

# ── SOURCE 4: REDDIT ──────────────────────────────────────────
REDDIT_SUBREDDITS = ['indiandefence', 'geopolitics', 'IndiaSpeaks']

def fetch_reddit_news() -> list:
    articles = []
    headers = {'User-Agent': 'DefencePostBot/1.0'}
    for subreddit in REDDIT_SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                posts = response.json().get('data', {}).get('children', [])
                for post in posts:
                    data = post.get('data', {})
                    if data.get('score', 0) > 50:
                        articles.append({
                            'title': data.get('title', ''),
                            'url': data.get('url', ''),
                            'source': f"r/{subreddit}",
                            'published': '',
                            'origin': 'Reddit',
                        })
        except Exception as e:
            log.error(f"Reddit error: {e}")
    return articles

# ── MAIN FETCHER ───────────────────────────────────────────────
def fetch_all_news(newsapi_key: str = '') -> list:
    log.info("Fetching news from all free sources...")
    all_articles = []
    
    # Run all sources
    all_articles.extend(fetch_gdelt_news())
    all_articles.extend(fetch_google_news_rss())
    if newsapi_key:
        all_articles.extend(fetch_newsapi(newsapi_key))
    all_articles.extend(fetch_reddit_news())

    deduplicated = deduplicate(all_articles)
    log.info(f"Total articles after dedup: {len(deduplicated)}")
    return deduplicated

def deduplicate(articles: list) -> list:
    seen_titles = set()
    unique = []
    for article in articles:
        title = article.get('title', '').lower().strip()
        key = ''.join(c for c in title[:60] if c.isalnum() or c.isspace())
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique.append(article)
    return unique
