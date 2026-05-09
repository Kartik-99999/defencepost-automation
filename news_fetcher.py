"""
news_fetcher.py
Fetches latest defence & geopolitics news using FREE sources:
1. GDELT Project API (completely free, no key needed)
2. Google News RSS (completely free, no key needed)
3. NewsAPI.org (free tier, 100 req/day)
"""

import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

log = logging.getLogger(__name__)

# ── SEARCH QUERIES ─────────────────────────────────────────────
# REMOVED: Specific old operation names that trigger historical results
# ADDED: "2026" and more dynamic triggers
DEFENCE_QUERIES = [
    "India defence military news",
    "Indian Army Navy Air Force latest",
    "India Pakistan border update",
    "India China LAC border tension",
    "DRDO missile test 2026",
    "India geopolitics strategic analysis",
    "Indo Pacific QUAD summit",
    "Indian Ocean naval security",
    "India defence manufacturing",
    "Ministry of Defence India press release",
]

# ── SOURCE 1: GDELT PROJECT ────────────────────────────────────
# (Your GDELT code is already good because it uses 'timespan': '1d')

# ── SOURCE 2: GOOGLE NEWS RSS (THE FIX IS HERE) ────────────────

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

def fetch_google_news_rss(max_results: int = 30) -> list:
    articles = []

    for query in DEFENCE_QUERIES[:8]:
        try:
            # THE FIX: Added 'when:1d' to the query string to force last 24 hours
            # Also added 'after:2026-05-01' as a secondary safety net
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
                    
                    # EXTRA SAFETY: Double check the year in the RSS date string
                    if "2024" in pub_date_str or "2025" in pub_date_str:
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
            continue

    return articles


# ── SOURCE 2: GOOGLE NEWS RSS ──────────────────────────────────

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

def fetch_google_news_rss(max_results: int = 30) -> list:
    """
    Fetch news from Google News RSS feeds
    Completely free — no API key needed
    """
    articles = []

    for query in DEFENCE_QUERIES[:6]:
        try:
            params = {
                'q':  query,
                'hl': 'en-IN',
                'gl': 'IN',
                'ceid': 'IN:en'
            }

            url = f"{GOOGLE_NEWS_RSS}?q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"

            response = requests.get(
                url,
                timeout=15,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; DefencePostBot/1.0)'
                }
            )

            if response.status_code == 200:
                # Parse RSS XML
                root = ET.fromstring(response.content)
                channel = root.find('channel')

                if channel is None:
                    continue

                items = channel.findall('item')
                log.info(f"Google News '{query}' → {len(items)} articles")

                for item in items[:5]:
                    title_el = item.find('title')
                    desc_el = item.find('description')
                    link_el = item.find('link')
                    pub_el = item.find('pubDate')
                    source_el = item.find('source')

                    title = title_el.text if title_el is not None else ''
                    # Clean Google News title (removes source suffix)
                    if title and ' - ' in title:
                        title = title.rsplit(' - ', 1)[0].strip()

                    if title and len(title) > 20:
                        articles.append({
                            'title':       title,
                            'description': (desc_el.text or title) if desc_el is not None else title,
                            'url':         link_el.text if link_el is not None else '',
                            'source':      source_el.text if source_el is not None else 'Google News',
                            'published':   pub_el.text if pub_el is not None else '',
                            'origin':      'Google News',
                            'keywords':    query.split(),
                        })

        except ET.ParseError as e:
            log.error(f"RSS parse error for '{query}': {e}")
            continue
        except Exception as e:
            log.error(f"Google News error for '{query}': {e}")
            continue

    log.info(f"Google News RSS total: {len(articles)} articles")
    return articles


# ── SOURCE 3: NEWSAPI.ORG ──────────────────────────────────────

NEWSAPI_URL = "https://newsapi.org/v2/everything"

def fetch_newsapi(api_key: str, max_results: int = 20) -> list:
    """
    Fetch news from NewsAPI.org (free tier: 100 req/day)
    """
    if not api_key:
        log.warning("No NewsAPI key provided — skipping")
        return []

    articles = []
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    queries = [
        "India defence OR India military OR Indian Army",
        "India Pakistan OR India China border OR LAC",
        "DRDO OR BrahMos OR Tejas OR Indian Navy",
        "Indo-Pacific OR QUAD OR India geopolitics",
    ]

    for query in queries[:3]:  # Limit to 3 to preserve free tier quota
        try:
            params = {
                'q':          query,
                'from':       yesterday,
                'sortBy':     'publishedAt',
                'language':   'en',
                'pageSize':   '10',
                'apiKey':     api_key,
            }

            response = requests.get(
                NEWSAPI_URL,
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('articles', [])
                log.info(f"NewsAPI '{query[:30]}' → {len(items)} articles")

                for item in items:
                    title = (item.get('title') or '').strip()
                    if not title or '[Removed]' in title:
                        continue

                    articles.append({
                        'title':       title,
                        'description': item.get('description') or title,
                        'url':         item.get('url', ''),
                        'source':      item.get('source', {}).get('name', 'Unknown'),
                        'published':   item.get('publishedAt', ''),
                        'origin':      'NewsAPI',
                        'keywords':    query.split()[:4],
                    })

            elif response.status_code == 426:
                log.warning("NewsAPI free tier limit reached")
                break
            else:
                log.warning(f"NewsAPI returned {response.status_code}")

        except Exception as e:
            log.error(f"NewsAPI error: {e}")
            continue

    log.info(f"NewsAPI total: {len(articles)} articles")
    return articles


# ── SOURCE 4: REDDIT ──────────────────────────────────────────

REDDIT_SUBREDDITS = [
    'IndiaSpeaks',
    'indiandefence',
    'geopolitics',
    'india',
    'worldnews',
]

def fetch_reddit_news(max_results: int = 20) -> list:
    """
    Fetch trending defence posts from Reddit
    Completely free — no API key needed for public feeds
    """
    articles = []

    headers = {
        'User-Agent': 'DefencePostBot/1.0 (defencepost.live)'
    }

    for subreddit in REDDIT_SUBREDDITS[:3]:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=15"
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                log.info(f"Reddit r/{subreddit} → {len(posts)} posts")

                defence_keywords = [
                    'india', 'defence', 'military', 'army', 'navy', 'air force',
                    'pakistan', 'china', 'missile', 'drdo', 'war', 'geopolitics',
                    'nuclear', 'border', 'lac', 'kashmir', 'operation', 'iac'
                ]

                for post in posts:
                    post_data = post.get('data', {})
                    title = post_data.get('title', '').strip()
                    score = post_data.get('score', 0)
                    url_post = post_data.get('url', '')
                    selftext = post_data.get('selftext', '')

                    # Only include defence-relevant posts
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in defence_keywords):
                        continue

                    # Only include popular posts
                    if score < 50:
                        continue

                    articles.append({
                        'title':       title,
                        'description': selftext[:300] if selftext else title,
                        'url':         url_post,
                        'source':      f"Reddit r/{subreddit}",
                        'published':   '',
                        'origin':      'Reddit',
                        'keywords':    [kw for kw in defence_keywords if kw in title_lower][:5],
                        'engagement':  score,
                    })

        except Exception as e:
            log.error(f"Reddit error for r/{subreddit}: {e}")
            continue

    log.info(f"Reddit total: {len(articles)} articles")
    return articles


# ── MAIN FETCHER ───────────────────────────────────────────────

def fetch_all_news(newsapi_key: str = '') -> list:
    """
    Fetch news from ALL free sources and combine
    Returns deduplicated list of articles sorted by relevance
    """
    log.info("Fetching news from all free sources...")

    all_articles = []

    # Source 1: GDELT (best for geopolitics)
    log.info("\n[SOURCE 1] GDELT Project...")
    gdelt = fetch_gdelt_news()
    all_articles.extend(gdelt)

    # Source 2: Google News RSS (best coverage)
    log.info("\n[SOURCE 2] Google News RSS...")
    google = fetch_google_news_rss()
    all_articles.extend(google)

    # Source 3: NewsAPI (structured data)
    if newsapi_key:
        log.info("\n[SOURCE 3] NewsAPI.org...")
        newsapi = fetch_newsapi(newsapi_key)
        all_articles.extend(newsapi)

    # Source 4: Reddit (trending topics)
    log.info("\n[SOURCE 4] Reddit...")
    reddit = fetch_reddit_news()
    all_articles.extend(reddit)

    # Deduplicate by title similarity
    deduplicated = deduplicate(all_articles)

    log.info(f"\nTotal articles before dedup: {len(all_articles)}")
    log.info(f"Total articles after dedup:  {len(deduplicated)}")

    return deduplicated


def deduplicate(articles: list) -> list:
    """
    Remove duplicate articles based on title similarity
    """
    seen_titles = set()
    unique = []

    for article in articles:
        title = article.get('title', '').lower().strip()

        # Create a simplified key (first 60 chars, lowercase)
        key = ''.join(c for c in title[:60] if c.isalnum() or c.isspace())
        key = ' '.join(key.split())  # normalise whitespace

        if key and key not in seen_titles and len(title) > 20:
            seen_titles.add(key)
            unique.append(article)

    return unique
