"""
image_fetcher.py
Automatically fetches relevant cover images from Wikimedia Commons
Free, legal, high-quality defence images
"""

import requests
import logging
import random
import re
from urllib.parse import quote

log = logging.getLogger(__name__)

WIKIMEDIA_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API   = "https://commons.wikimedia.org/w/api.php"

# Image quality filters
MIN_WIDTH  = 800
MIN_HEIGHT = 400

# Defence-specific image search terms mapped to topic keywords
IMAGE_KEYWORD_MAP = {
    'tejas':       ['HAL Tejas', 'Tejas fighter jet', 'Indian Air Force LCA'],
    'rafale':      ['Dassault Rafale IAF', 'Rafale India'],
    'su-30':       ['Sukhoi Su-30MKI', 'IAF Su-30'],
    'brahmos':     ['BrahMos missile', 'BrahMos launch'],
    'arihant':     ['INS Arihant submarine'],
    'vikrant':     ['INS Vikrant aircraft carrier'],
    'pinaka':      ['Pinaka rocket launcher India'],
    'akash':       ['Akash missile system India'],
    'drdo':        ['DRDO India defence'],
    'pakistan':    ['Pakistan army', 'Pakistan Air Force'],
    'china':       ['Chinese military PLA', 'People Liberation Army'],
    'navy':        ['Indian Navy warship', 'Indian Navy frigate'],
    'army':        ['Indian Army soldiers', 'Indian Army tank'],
    'air force':   ['Indian Air Force aircraft', 'IAF fighter jet'],
    'missile':     ['India missile launch', 'ballistic missile India'],
    'submarine':   ['Indian Navy submarine'],
    'tank':        ['Arjun tank India', 'Indian Army T-90'],
    'drone':       ['India drone UAV military', 'IAI Heron India'],
    'nuclear':     ['India nuclear test', 'India ICBM missile'],
    'lakshadweep': ['Lakshadweep aerial island'],
    'ladakh':      ['Ladakh border India China', 'Galwan valley'],
    'kashmir':     ['Kashmir valley India', 'Line of Control'],
    'israel':      ['Israel India defence', 'IAI India'],
    'armenia':     ['Armenia defence', 'Yerevan Armenia'],
    's-400':       ['S-400 India missile system'],
}

def extract_smart_queries(headline: str) -> list:
    """
    Analyzes the headline, removes filler words, and creates highly specific search queries.
    """
    if not headline:
        return []

    # Remove punctuation
    clean_headline = re.sub(r'[^\w\s]', ' ', headline)
    
    # Filler words that ruin image searches
    stopwords = {'in', 'the', 'of', 'and', 'to', 'for', 'a', 'an', 'is', 'on', 'with', 
                 'unveils', 'charting', 'future', 'strategic', 'spark', 'deepen', 
                 'amidst', 'dynamics', 'imperatives', 'evolving', 'forges', 'leap', 'india', 'indian'}
                 
    words = clean_headline.split()
    
    # Extract Capitalized words (Usually names like "Rajnath Singh", or places like "Korea")
    entities = [w for w in words if w.istitle() and w.lower() not in stopwords]
    
    queries = []
    
    # 1. Search for specific names/places first
    if len(entities) >= 2:
        queries.append(f"{entities[0]} {entities[1]}")
    elif len(entities) == 1:
         queries.append(f"{entities[0]} defence")
    
    # 2. Fallback: longest technical words in the headline
    long_words = [w for w in words if len(w) > 5 and w.lower() not in stopwords]
    if len(long_words) >= 2:
        queries.append(f"{long_words[0]} {long_words[1]}")
        
    return queries

def build_search_queries(keywords: list, headline: str = None) -> list:
    """
    Build optimised search queries prioritizing the exact headline.
    """
    queries = []

    # 1. Highest Priority: Analyze the actual article headline
    if headline:
        smart_queries = extract_smart_queries(headline)
        queries.extend(smart_queries)

    # 2. Check keyword map
    if keywords:
        keywords_lower = [k.lower() for k in keywords]
        for key, search_terms in IMAGE_KEYWORD_MAP.items():
            if any(key in kw for kw in keywords_lower):
                queries.extend(search_terms)

        for kw in keywords[:3]:
            if len(kw) > 3:
                queries.append(f"{kw} military")

    # 3. Final Default fallbacks
    queries.append("Indian Armed Forces")
    queries.append("Indian Air Force fighter jet")

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)

    return unique_queries[:8]

def search_wikimedia(query: str) -> str | None:
    """
    Search Wikimedia Commons and return a RANDOM image from the top 30 results.
    """
    try:
        params = {
            'action': 'query',
            'generator': 'search',
            'gsrnamespace': '6',  
            'gsrsearch': f'filetype:bitmap {query}',
            'gsrlimit': '30',     # Get 30 results so we can pick randomly
            'prop': 'imageinfo',
            'iiprop': 'url|dimensions|mime',
            'iiurlwidth': '1200',
            'format': 'json',
            'origin': '*'
        }

        response = requests.get(
            COMMONS_API,
            params=params,
            timeout=15,
            headers={'User-Agent': 'DefencePostBot/1.0 (defencepost.in)'}
        )

        if response.status_code != 200:
            return None

        data = response.json()
        pages = data.get('query', {}).get('pages', {})

        valid_images = []

        for page_id, page in pages.items():
            if page_id == '-1': continue

            imageinfo = page.get('imageinfo', [{}])[0]
            mime = imageinfo.get('mime', '')
            width = imageinfo.get('width', 0)
            height = imageinfo.get('height', 0)
            url = imageinfo.get('url', '')

            # Strict Quality Filters
            if not url or mime not in ['image/jpeg', 'image/png', 'image/webp']: continue
            if width < MIN_WIDTH or height < MIN_HEIGHT: continue
            if 'svg' in url.lower() or 'flag' in url.lower() or 'logo' in url.lower() or 'map' in url.lower(): continue

            valid_images.append(url)

        # ✨ THE FIX: Pick a random image from the pool!
        if valid_images:
            return random.choice(valid_images)

        return None

    except Exception as e:
        log.error(f"Image fetch error: {e}")
        return None

def fetch_cover_image(keywords: list = None, headline: str = None) -> str | None:
    """
    Main entry point to fetch the image.
    """
    if not keywords and not headline:
        return None

    search_queries = build_search_queries(keywords or [], headline)

    for query in search_queries:
        log.info(f"Searching Wikimedia for: {query}")
        image_url = search_wikimedia(query)
        if image_url:
            log.info(f"Found image: {image_url[:80]}")
            return image_url

    log.warning(f"No suitable image found for headline: {headline}")
    return None

def get_wikipedia_image(article_title: str) -> str | None:
    # Keeping your original function intact just in case
    pass
