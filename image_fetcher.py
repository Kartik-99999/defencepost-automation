"""
image_fetcher.py
Automatically fetches relevant cover images from Wikimedia Commons
Free, legal, high-quality defence images
"""

import requests
import logging
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


def fetch_cover_image(keywords: list) -> str | None:
    """
    Search Wikimedia Commons for a relevant defence image
    Returns the direct image URL or None if not found
    """
    if not keywords:
        return None

    # Build search queries from keywords
    search_queries = build_search_queries(keywords)

    for query in search_queries:
        log.info(f"Searching Wikimedia for: {query}")
        image_url = search_wikimedia(query)
        if image_url:
            log.info(f"Found image: {image_url[:80]}")
            return image_url

    log.warning(f"No suitable image found for keywords: {keywords}")
    return None


def build_search_queries(keywords: list) -> list:
    """
    Build optimised search queries from article keywords
    """
    queries = []

    # Check keyword map first for better results
    keywords_lower = [k.lower() for k in keywords]
    for key, search_terms in IMAGE_KEYWORD_MAP.items():
        if any(key in kw for kw in keywords_lower):
            queries.extend(search_terms)

    # Add direct keyword searches
    for kw in keywords[:3]:
        if len(kw) > 3:
            queries.append(f"{kw} India defence military")

    # Default fallback
    queries.append("Indian Armed Forces military")
    queries.append("Indian Air Force fighter jet")

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)

    return unique_queries[:8]  # Max 8 attempts


def search_wikimedia(query: str) -> str | None:
    """
    Search Wikimedia Commons for an image matching the query
    Returns direct image URL or None
    """
    try:
        # Search Commons for images
        params = {
            'action': 'query',
            'generator': 'search',
            'gsrnamespace': '6',  # File namespace
            'gsrsearch': f'filetype:bitmap {query}',
            'gsrlimit': '10',
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

        # Find best image
        for page_id, page in pages.items():
            if page_id == '-1':
                continue

            imageinfo = page.get('imageinfo', [{}])[0]
            mime = imageinfo.get('mime', '')
            width = imageinfo.get('width', 0)
            height = imageinfo.get('height', 0)
            url = imageinfo.get('url', '')

            # Quality filters
            if not url:
                continue
            if mime not in ['image/jpeg', 'image/png', 'image/webp']:
                continue
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                continue
            # Skip SVG and non-photo files
            if 'svg' in url.lower() or 'flag' in url.lower():
                continue

            return url

        return None

    except requests.RequestException as e:
        log.error(f"Wikimedia request failed: {e}")
        return None
    except Exception as e:
        log.error(f"Image fetch error: {e}")
        return None


def get_wikipedia_image(article_title: str) -> str | None:
    """
    Get the main image from a Wikipedia article
    Alternative method for well-known topics
    """
    try:
        params = {
            'action': 'query',
            'titles': article_title,
            'prop': 'pageimages',
            'pithumbsize': '1200',
            'format': 'json',
            'origin': '*'
        }

        response = requests.get(
            WIKIMEDIA_API,
            params=params,
            timeout=10,
            headers={'User-Agent': 'DefencePostBot/1.0'}
        )

        if response.status_code != 200:
            return None

        data = response.json()
        pages = data.get('query', {}).get('pages', {})

        for page_id, page in pages.items():
            if page_id == '-1':
                continue
            thumb = page.get('thumbnail', {})
            source = thumb.get('source', '')
            if source and thumb.get('width', 0) >= MIN_WIDTH:
                return source

        return None

    except Exception as e:
        log.error(f"Wikipedia image fetch error: {e}")
        return None
