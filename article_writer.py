"""
article_writer.py
Writes full SEO-optimised defence articles using
Google Gemini API (completely FREE)
"""

import json
import logging
import re
import google.generativeai as genai

log = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a senior defence journalist writing for DefencePost.in — India's premier independent defence journalism platform.

Your writing style:
- Authoritative, analytical, deeply informed
- Written from India's strategic perspective
- Proper military terminology and technical accuracy
- Minimum 1200 words, ideally 1500+ words
- SEO optimised with natural keyword integration

FORMATTING RULES — VERY IMPORTANT:
- Use HTML tags: <p>, <h2>, <h3>, <ul>, <li>, <strong>
- Do NOT use markdown (no # ## ### * ** -)
- Every major section needs <h2> heading
- At least 3 <h3> subheadings
- Bold important terms: <strong>term</strong>
- Use <ul><li> for lists
- Wrap every paragraph in <p></p>"""

ARTICLE_PROMPT = """Write a comprehensive SEO-optimised defence article for DefencePost.in.

TOPIC: {title}
CATEGORY: {category}
INDIA ANGLE: {india_relevance}
ORIGINAL NEWS: {original_headline}
ARTICLE APPROACH: {article_angle}
KEYWORDS TO INCLUDE: {keywords}

Write:
1. Full article body in HTML (minimum 1200 words)
2. Use <h2> for main sections, <h3> for subsections
3. Bold all weapons systems, technical terms, organisation names
4. Include specific facts, figures, capabilities, ranges
5. Analyse implications for India throughout
6. End article with: <p><em>DefencePost.in covers Indian defence and strategic affairs. Read more in our {category} section.</em></p>

Respond ONLY in this exact JSON format, no markdown fences, no extra text:
{{
  "title": "Full compelling SEO title (max 100 chars)",
  "content": "<h2>First Section</h2><p>Content here...</p><h2>Second Section</h2>...",
  "excerpt": "SEO meta description under 160 chars",
  "author": "Kartik Bhardwaj",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "readTime": 7,
  "category": "{category}",
  "status": "published",
  "featured": false
}}"""


def write_article(topic: dict, gemini_api_key: str) -> dict | None:
    """
    Write full article using Gemini 2.5 Flash (free)
    """
    if not gemini_api_key:
        log.error("No Gemini API key")
        return None

    if not topic.get('title'):
        log.error("No title in topic")
        return None

    # Configure Gemini
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=SYSTEM_INSTRUCTION
    )

    prompt = ARTICLE_PROMPT.format(
        title=topic.get('title', ''),
        category=topic.get('category', 'Military'),
        india_relevance=topic.get('india_relevance', ''),
        original_headline=topic.get('original_headline', ''),
        article_angle=topic.get('article_angle', 'India strategic perspective'),
        keywords=', '.join(topic.get('keywords', []))
    )

    try:
        log.info(f"Writing article with Gemini: {topic['title'][:60]}...")

        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 4096,
            }
        )

        response_text = response.text.strip()

        # Clean markdown fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()

        # Parse JSON
        try:
            article = json.loads(response_text)

            # Validate required fields
            required = ['title', 'content', 'excerpt', 'category']
            missing = [f for f in required if not article.get(f)]
            if missing:
                log.error(f"Missing fields: {missing}")
                return None

            # Ensure tags is a list
            if isinstance(article.get('tags'), str):
                article['tags'] = [t.strip() for t in article['tags'].split(',')]

            # Add defaults
            article.setdefault('author', 'Kartik Bhardwaj')
            article.setdefault('status', 'published')
            article.setdefault('featured', False)

            # Calculate read time
            word_count = len(re.sub(r'<[^>]+>', '', article.get('content', '')).split())
            article['readTime'] = article.get('readTime') or max(1, word_count // 200)

            log.info(f"✅ Article written:")
            log.info(f"   Title: {article['title'][:70]}")
            log.info(f"   Words: ~{word_count}")
            log.info(f"   Tags:  {len(article.get('tags', []))}")
            log.info(f"   Read:  {article['readTime']} min")

            return article

        except json.JSONDecodeError as e:
            log.error(f"JSON parse error: {e}")
            log.error(f"Response start: {response_text[:300]}")
            return None

    except Exception as e:
        log.error(f"Gemini article writing error: {e}")
        return None
