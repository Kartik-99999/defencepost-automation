"""
publisher.py
Publishes AI-written articles to DefencePost.in
via the backend REST API
"""

import requests
import logging
import time

log = logging.getLogger(__name__)

TIMEOUT = 60  # seconds — backend may be sleeping on Render free tier


def get_auth_token(backend_url: str, email: str, password: str) -> str | None:
    """
    Authenticate with DefencePost backend and get JWT token
    """
    try:
        url = f"{backend_url}/auth/login"
        payload = {"email": email, "password": password}

        log.info(f"Authenticating with backend: {url}")

        # Backend may be sleeping — give it time to wake up
        for attempt in range(3):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=TIMEOUT,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    data = response.json()
                    token = data.get('token', '')
                    if token:
                        log.info("Authentication successful")
                        return token
                    else:
                        log.error(f"No token in response: {data}")
                        return None

                elif response.status_code == 503:
                    log.warning(f"Backend sleeping (attempt {attempt+1}/3). Waiting 30s...")
                    time.sleep(30)
                    continue

                else:
                    log.error(f"Auth failed: {response.status_code} — {response.text[:200]}")
                    return None

            except requests.Timeout:
                log.warning(f"Backend timeout (attempt {attempt+1}/3). Retrying...")
                time.sleep(20)
                continue

        log.error("Authentication failed after 3 attempts")
        return None

    except Exception as e:
        log.error(f"Unexpected error during authentication: {e}")
        return None


def publish_article(
    article: dict,
    backend_url: str,
    email: str,
    password: str
) -> bool:
    """
    Publish article to DefencePost.in via backend API
    Returns True if successful, False otherwise
    """
    # Step 1: Authenticate
    token = get_auth_token(backend_url, email, password)
    if not token:
        log.error("Cannot publish — authentication failed")
        return False

    # Step 2: Prepare article payload
    payload = {
        'title':      article.get('title', ''),
        'content':    article.get('content', ''),
        'excerpt':    article.get('excerpt', ''),
        'author':     article.get('author', 'Kartik Bhardwaj'),
        'category':   article.get('category', 'Military'),
        'tags':       article.get('tags', []),
        'coverImage': article.get('coverImage', ''),
        'status':     article.get('status', 'published'),
        'featured':   article.get('featured', False),
        'readTime':   article.get('readTime', 5),
    }

    # Validate required fields
    if not payload['title']:
        log.error("Article title is empty — cannot publish")
        return False
    if not payload['content']:
        log.error("Article content is empty — cannot publish")
        return False
    if len(payload['content']) < 500:
        log.error(f"Article content too short: {len(payload['content'])} chars")
        return False

    # Ensure tags is a list
    if isinstance(payload['tags'], str):
        payload['tags'] = [t.strip() for t in payload['tags'].split(',') if t.strip()]

    # Step 3: Post article to backend
    try:
        url = f"{backend_url}/articles"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        log.info(f"Publishing article: {payload['title'][:60]}...")
        log.info(f"Category: {payload['category']}")
        log.info(f"Status: {payload['status']}")
        log.info(f"Tags: {payload['tags'][:5]}")

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=TIMEOUT
        )

        if response.status_code in [200, 201]:
            data = response.json()
            article_id = data.get('article', {}).get('_id', 'unknown')
            article_slug = data.get('article', {}).get('slug', 'unknown')
            log.info(f"Article published successfully!")
            log.info(f"  ID: {article_id}")
            log.info(f"  Slug: {article_slug}")
            log.info(f"  URL: /article/{article_slug}")
            return True

        else:
            log.error(f"Publish failed: {response.status_code}")
            log.error(f"Response: {response.text[:500]}")
            return False

    except requests.Timeout:
        log.error(f"Publish request timed out after {TIMEOUT}s")
        return False

    except requests.RequestException as e:
        log.error(f"Publish request failed: {e}")
        return False

    except Exception as e:
        log.error(f"Unexpected error during publishing: {e}")
        return False


def check_backend_health(backend_url: str) -> bool:
    """
    Check if backend is alive (handles Render free tier sleeping)
    """
    try:
        health_url = f"{backend_url}/health"
        log.info(f"Checking backend health: {health_url}")

        response = requests.get(health_url, timeout=65)  # 65s allows Render to wake up
        if response.status_code == 200:
            log.info("Backend is healthy")
            return True
        else:
            log.warning(f"Backend health check returned: {response.status_code}")
            return False

    except requests.Timeout:
        log.warning("Backend health check timed out — may be sleeping")
        return False
    except Exception as e:
        log.error(f"Health check error: {e}")
        return False
