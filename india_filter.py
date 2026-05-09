"""
india_filter.py
Uses Google Gemini API (FREE) to prioritise defence news
from India's strategic perspective
"""

import json
import logging
import re
import google.generativeai as genai

log = logging.getLogger(__name__)

CATEGORIES = [
    'Military', 'Geopolitics', 'Naval',
    'Cyber & Tech', 'Intelligence', 'Policy', 'Press Release'
]

PRIORITY_PROMPT = """You are a senior Indian defence analyst and strategic affairs expert writing for DefencePost.in.

I will give you a list of defence and geopolitics news headlines from the last 24 hours.

Your task:
1. Analyse each headline from INDIA's strategic perspective
2. Score each 1-10 on relevance to India (10 = extremely important)
3. Select the TOP {n} most important for Indian readers
4. For each selected topic provide a complete article brief

SCORING CRITERIA (highest priority first):
- Direct India security threat or opportunity (10)
- India-Pakistan military/terror developments (9)
- India-China LAC/border/naval developments (9)
- Indian military capability (IAF/Army/Navy/DRDO) (8)
- India strategic partnerships (US/Russia/Israel/France) (7)
- Indo-Pacific/QUAD/Indian Ocean developments (7)
- Regional conflicts affecting India (6)
- Global defence developments relevant to India (5)

NEWS HEADLINES:
{headlines}

Respond ONLY with valid JSON, no markdown, no explanation:
{{
  "prioritised": [
    {{
      "title": "Compelling SEO article title from India perspective (max 100 chars)",
      "category": "one of: Military, Geopolitics, Naval, Cyber & Tech, Intelligence, Policy",
      "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
      "india_relevance": "2 sentences why this matters to India strategically",
      "india_score": 8,
      "original_headline": "original news headline",
      "article_angle": "specific angle for the article from India's POV"
    }}
  ]
}}"""


def prioritise_for_india(articles: list, gemini_api_key: str, n: int = 1) -> list:
    """
    Use Gemini to prioritise news from India's strategic perspective
    """
    if not articles:
        log.warning("No articles to prioritise")
        return []

    if not gemini_api_key:
        log.error("No Gemini API key provided")
        return fallback_prioritise(articles[:n])

    # Configure Gemini
    genai.configure(api_key=gemini_api_key)
    # Updated to gemini-2.5-flash
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Format headlines for prompt
    headlines_text = ""
    for i, article in enumerate(articles[:25], 1):
        title = article.get('title', '').strip()
        source = article.get('source', '')
        origin = article.get('origin', '')
        desc = article.get('description', '')[:100]

        if title:
            headlines_text += f"\n{i}. [{origin}/{source}] {title}"
            if desc and desc != title:
                headlines_text += f"\n   Context: {desc}"

    prompt = PRIORITY_PROMPT.format(
        n=n,
        headlines=headlines_text
    )

    try:
        log.info("Sending headlines to Gemini for India prioritisation...")

        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 2000,
            }
        )

        response_text = response.text.strip()

        # Clean up any markdown code fences
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()

        # Parse JSON
        try:
            result = json.loads(response_text)
            prioritised = result.get('prioritised', [])

            log.info(f"Gemini prioritised {len(prioritised)} topics:")
            for i, topic in enumerate(prioritised, 1):
                log.info(
                    f"  {i}. [{topic.get('india_score', '?')}/10] "
                    f"{topic.get('title', 'Unknown')[:70]}"
                )

            return prioritised

        except json.JSONDecodeError as e:
            log.error(f"Failed to parse Gemini JSON: {e}")
            log.error(f"Raw: {response_text[:500]}")
            return fallback_prioritise(articles[:n])

    except Exception as e:
        log.error(f"Gemini API error: {e}")
        return fallback_prioritise(articles[:n])


def fallback_prioritise(articles: list) -> list:
    """Keyword-based fallback if Gemini fails"""
    log.info("Using keyword fallback prioritisation")

    india_kws = [
        'india', 'indian', 'modi', 'iaf', 'drdo', 'hal', 'brahmos',
        'tejas', 'pakistan', 'china', 'lac', 'kashmir', 'quad',
        'indo-pacific', 'indian ocean', 'arihant', 'vikrant'
    ]

    scored = []
    for a in articles:
        text = (a.get('title', '') + ' ' + a.get('description', '')).lower()
        score = sum(1 for kw in india_kws if kw in text)
        scored.append({**a, '_score': score})

    scored.sort(key=lambda x: x['_score'], reverse=True)

    return [{
        'title': a.get('title', 'Defence News Update'),
        'category': 'Military',
        'keywords': a.get('keywords', ['India', 'Defence', 'Military'])[:5],
        'india_relevance': a.get('description', '')[:200],
        'india_score': a.get('_score', 5),
        'original_headline': a.get('title', ''),
        'article_angle': 'India strategic perspective analysis'
    } for a in scored[:3]]
