# DefencePost.in — AI Article Automation (100% FREE)

Automatically generates and publishes SEO defence articles daily.

## Cost: ZERO ₹

| Component | Tool | Cost |
|-----------|------|------|
| News Source | Google News RSS + GDELT + Reddit | FREE |
| AI Writer | Google Gemini 1.5 Flash | FREE |
| Images | Wikimedia Commons | FREE |
| Automation | GitHub Actions | FREE |
| Backend | Your existing Render.com | FREE |

## How It Works

```
Google News RSS (free)
GDELT Project (free)          → Fetch last 24hr defence news
Reddit r/indiandefence (free)
         ↓
Google Gemini 1.5 Flash       → Prioritise for India
         ↓
Google Gemini 1.5 Flash       → Write 1200+ word SEO article
         ↓
Wikimedia Commons             → Find cover image
         ↓
DefencePost Backend API       → Publish article
         ↓
defencepost.live ✅           → Article is live!
```

## Setup (10 minutes)

### Step 1: Create GitHub repo
Create a NEW private repo on github.com (e.g. `defencepost-automation`)
Upload all these files to it.

### Step 2: Add GitHub Secrets
Go to: `Settings → Secrets and variables → Actions → New repository secret`

| Secret Name | Value | Where to get |
|-------------|-------|--------------|
| `GEMINI_API_KEY` | AIza... | aistudio.google.com → Get API Key |
| `NEWSAPI_KEY` | abc123... | newsapi.org → Free signup (optional) |
| `BACKEND_URL` | https://defencepost-backend-e9fn.onrender.com/api | Your backend |
| `ADMIN_EMAIL` | admin@defencepost.in | Your admin email |
| `ADMIN_PASSWORD` | DefencePost@2026 | Your admin password |

### Step 3: Enable GitHub Actions
Go to: `Actions tab → Enable workflows`

### Step 4: Test it!
Go to: `Actions → DefencePost Daily AI Article Generator → Run workflow`

## Schedule
Runs automatically at **6:00 AM IST every day**

## Manual Trigger
GitHub Actions UI → Run workflow → Choose 1-3 articles

## Manual Writing
Admin panel at `/admin/index.html` always available.
This automation runs ALONGSIDE manual writing.

## Files
```
defencepost-auto-v2/
├── main.py              ← Main orchestrator
├── news_fetcher.py      ← Fetches from Google News/GDELT/Reddit
├── india_filter.py      ← Gemini prioritises for India
├── article_writer.py    ← Gemini writes the article
├── image_fetcher.py     ← Wikimedia cover image
├── publisher.py         ← Posts to DefencePost backend
├── requirements.txt     ← pip install -r requirements.txt
└── .github/
    └── workflows/
        └── daily.yml    ← GitHub Actions schedule
```
