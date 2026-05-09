"""
india_filter.py
Prioritises the most common and strategic defence news for DefencePost.in.
Includes frequency analysis to identify daily trending topics.
"""

import json
import logging
import re
from collections import Counter
import google.generativeai as genai

log = logging.getLogger(__name__)

CATEGORIES = [
    'Military', 'Geopolitics', 'Naval',
    'Cyber & Tech', 'Intelligence', 'Policy', 'Press Release'
]

# Updated prompt to focus on "Dominant Narratives"
PRIORITY_PROMPT = """You are a senior Indian defence analyst. 
Today is May 9, 2026.

I will provide a list of trending defence headlines. 
Your task:
1. Identify the 'Dominant Narrative' (the topic reported by the most sources).
2. If the 'Operation Sindoor' anniversary is trending, prioritise it.
3. Select the TOP {n} topic that has the highest strategic impact for India.

NEWS HEADLINES:
{headlines}

Respond ONLY with valid JSON:
{{
  "prioritised": [
    {{
      "title": "Compelling SEO title (max 100 chars)",
      "category": "one of: Military, Geopolitics, Naval, Cyber & Tech, Intelligence, Policy",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "india_relevance": "Strategic significance in 2 sentences",
      "india_score": 10,
      "original_headline": "original news headline",
      "article_angle": "The 'most-common-topic' angle for today"
    }}
  ]
}}"""

def get_trending_context(articles, top_n=10):
    """Zero-cost Python logic to find the most common daily topics."""
    text = " ".join([a.get('title', '') for a in articles]).lower()
    words = re.findall(r'\w+', text)
    # Filter out generic stop words
    stop_words = {'india', 'defence', 'military', 'news', 'latest', 'with', 'over', 'from', 'against'}
    filtered = [w for w in words if w not in stop_words and len(w) > 3]
    
    common = [word for word, count in Counter(filtered).most_common(top_n)]
    log.info(f"Top trending keywords identified: {', '.join(common)}")
    return common

def prioritise_for_india(articles: list, gemini_api_key: str, n: int = 1) -> list:
    if not articles:
        return []

    # Step 1: Identify trending keywords without using API quota
    trending_keywords = get_trending_context(articles)
    
    # Step 2: Pre-filter articles that contain these trending keywords
    # This ensures we only send the 'most common' stories to Gemini
    filtered_articles = []
    for a in articles:
        if any(kw in a.get('title', '').lower() for kw in trending_keywords[:5]):
            filtered_articles.append(a)
    
    # Use filtered list or fallback to top of the stack if none found
    target_articles = filtered_articles[:15] if filtered_articles else articles[:15]

    if not gemini_api_key:
        log.error("No API key — using fallback")
        return fallback_prioritise(target_articles[:n])

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    headlines_text = ""
    for i, article in enumerate(target_articles, 1):
        headlines_text += f"\n{i}. [{article.get('source', 'News')}] {article.get('title', '')}"

    prompt = PRIORITY_PROMPT.format(n=n, headlines=headlines_text)

    try:
        log.info(f"Requesting prioritisation for the most common topics...")
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.2, # Lower temperature for more consistent JSON
                'max_output_tokens': 1000,
                'response_mime_type': 'application/json',
            }
        )

        response_text = response.text.strip()
        # Single-line regex to avoid SyntaxErrors
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^
```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        result = json.loads(response_text)
        return result.get('prioritised', [])

    except Exception as e:
        log.error(f"Priority Error: {e}")
        return fallback_prioritise(target_articles[:n])

def fallback_prioritise(articles: list) -> list:
    log.info("Using keyword fallback prioritisation")
    # Simple score based on 'India' relevance
    for a in articles:
        a['_score'] = 10 if 'operation sindoor' in a.get('title', '').lower() else 5
    articles.sort(key=lambda x: x.get('_score', 0), reverse=True)
    
    return [{
        'title': articles[0].get('title', 'Daily Defence Update'),
        'category': 'Military',
        'keywords': ['India', 'Defence'],
        'india_relevance': 'High frequency topic identified across sources.',
        'india_score': 8,
        'original_headline': articles[0].get('title', ''),
        'article_angle': 'Commonality-based strategic report'
    }]
