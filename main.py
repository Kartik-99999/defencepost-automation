#!/usr/bin/env python3
"""
DefencePost.in — AI Article Automation Engine v2
FREE VERSION — Uses:
  - Google News RSS + GDELT + Reddit (free news sources)
  - Google Gemini 1.5 Flash (free AI)
  - Wikimedia Commons (free images)
  - DefencePost backend API (your own)
"""

import os
import sys
import logging
from datetime import datetime

from news_fetcher import fetch_all_news
from india_filter import prioritise_for_india
from article_writer import write_article
from image_fetcher import fetch_cover_image
from publisher import publish_article, check_backend_health

# ── LOGGING ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ── CONFIG FROM ENV ────────────────────────────────────────────
GEMINI_API_KEY   = os.environ.get('GEMINI_API_KEY', '')
NEWSAPI_KEY      = os.environ.get('NEWSAPI_KEY', '')       # Optional
BACKEND_URL      = os.environ.get('BACKEND_URL', 'https://defencepost-backend-e9fn.onrender.com/api')
ADMIN_EMAIL      = os.environ.get('ADMIN_EMAIL', 'admin@defencepost.in')
ADMIN_PASSWORD   = os.environ.get('ADMIN_PASSWORD', '')
ARTICLES_PER_DAY = int(os.environ.get('ARTICLES_PER_DAY', '1'))


def main():
    log.info("=" * 65)
    log.info("  DefencePost.in AI Automation Engine v2 (FREE)")
    log.info(f"  Date: {datetime.now().strftime('%d %B %Y — %H:%M')}")
    log.info(f"  Articles to generate: {ARTICLES_PER_DAY}")
    log.info("=" * 65)

    # ── Validate required config ───────────────────────────────
    errors = []
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY not set")
    if not ADMIN_PASSWORD:
        errors.append("ADMIN_PASSWORD not set")

    if errors:
        for err in errors:
            log.error(f"❌ {err}")
        log.error("Set these in GitHub Secrets. Exiting.")
        sys.exit(1)

    # ── STEP 1: Wake up Render backend ────────────────────────
    log.info("\n[STEP 1] Waking up DefencePost backend...")
    is_healthy = check_backend_health(BACKEND_URL)
    if not is_healthy:
        log.warning("Backend may be slow to respond — will retry during publish")

    # ── STEP 2: Fetch news from all free sources ───────────────
    log.info("\n[STEP 2] Fetching latest defence news (free sources)...")
    all_news = fetch_all_news(newsapi_key=NEWSAPI_KEY)

    if not all_news:
        log.error("❌ No news fetched from any source. Exiting.")
        sys.exit(1)

    log.info(f"✅ Fetched {len(all_news)} unique articles total")

    # ── STEP 3: Prioritise for India using Gemini ──────────────
    log.info(f"\n[STEP 3] Prioritising top {ARTICLES_PER_DAY} topics for India...")
    prioritised = prioritise_for_india(
        articles=all_news,
        gemini_api_key=GEMINI_API_KEY,
        n=ARTICLES_PER_DAY + 2  # Extra buffer in case some fail
    )

    if not prioritised:
        log.error("❌ No topics prioritised. Exiting.")
        sys.exit(1)

    log.info(f"✅ {len(prioritised)} topics prioritised from India's perspective")

    # ── STEP 4-7: Write and publish articles ───────────────────
    published_count = 0

    for i, topic in enumerate(prioritised):
        if published_count >= ARTICLES_PER_DAY:
            break

        log.info(f"\n{'─' * 50}")
        log.info(f"[ARTICLE {i+1}] {topic.get('title', 'Unknown')[:70]}")
        log.info(f"Category: {topic.get('category', 'Military')}")
        log.info(f"India Score: {topic.get('india_score', '?')}/10")
        log.info(f"{'─' * 50}")

        # STEP 4: Write article with Gemini
        log.info(f"\n[STEP 4] Writing article...")
        article = write_article(topic, GEMINI_API_KEY)

        if not article:
            log.warning(f"⚠️  Failed to write article. Trying next topic...")
            continue

        # STEP 5: Fetch cover image from Wikimedia
        log.info(f"\n[STEP 5] Finding cover image...")
        cover_image = fetch_cover_image(
            keywords=topic.get('keywords', []), 
            headline=topic.get('title', '')
        )
        if cover_image:
            article['coverImage'] = cover_image
            log.info(f"✅ Cover image found")
        else:
            log.warning("⚠️  No cover image found — publishing without image")

        # STEP 6: Publish to DefencePost.in
        log.info(f"\n[STEP 6] Publishing to DefencePost.in...")
        success = publish_article(
            article=article,
            backend_url=BACKEND_URL,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD
        )

        if success:
            published_count += 1
            log.info(f"✅ Article {published_count}/{ARTICLES_PER_DAY} published!")
        else:
            log.error(f"❌ Failed to publish. Trying next topic...")

    # ── Summary ────────────────────────────────────────────────
    log.info("\n" + "=" * 65)
    log.info(f"  AUTOMATION COMPLETE")
    log.info(f"  Published: {published_count}/{ARTICLES_PER_DAY} articles")
    log.info(f"  Time: {datetime.now().strftime('%d %B %Y — %H:%M')}")
    log.info("=" * 65)

    if published_count == 0:
        log.error("No articles published — check errors above")
        sys.exit(1)


if __name__ == '__main__':
    main()
