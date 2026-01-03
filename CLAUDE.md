# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Auto-Arxiv-Subscription is an automated ArXiv paper notification system that sends daily emails with papers matching specified keywords. It runs on GitHub Actions with no server required.

The system:
1. Fetches today's papers from ArXiv RSS feeds (cs.AI, cs.CV, cs.CG, cs.CL, stat.ML)
2. Filters papers by user-defined keywords (case-insensitive title matching)
3. Optionally enhances papers using AI (DashScope API) for:
   - Chinese translation of abstracts
   - Keyword extraction
   - Main contribution summary
4. Sends formatted HTML email via SMTP

## Environment Setup

### Required Environment Variables

Set these in GitHub Secrets (Settings → Secrets → Actions) or in a local `.env` file:

- `EMAIL` - Sender email (QQ Mail recommended)
- `EMAIL_TOKEN` - Email app password/authorization code
- `RECEIVER_EMAIL` - Recipient email address
- `KEYWORDS` - Space-separated search keywords (e.g., "3D BEV occupancy detection")
- `DASHSCOPE_API_KEY` - Alibaba DashScope API key for AI enhancement
- `OPENAI_MODEL` - AI model to use (default: "qwen3-max-preview")

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally with environment variables
python src/main.py --email YOUR_EMAIL --token YOUR_TOKEN --receiver RECEIVER_EMAIL --keywords keyword1 keyword2
```

## Architecture

### Main Components

**`src/main.py`** - Single-file application containing:

- **Data Fetching**: `get_arxiv_data()` - Scrapes ArXiv RSS feeds for papers published today
- **Keyword Filtering**: `filter_keywords()` - Matches papers against keywords (case-insensitive substring match in titles)
- **AI Processing**: `process_abstract_with_ai()` - Uses DashScope API to translate abstracts, extract keywords, and summarize contributions
- **Email Generation**: Creates styled HTML with:
  - Collapsible sections for each keyword
  - Paper details with AI-enhanced content
  - Color-coded sections (8 predefined color schemes rotated)
- **Email Sending**: `sendEmail()` - Sends via QQ Mail SMTP (smtp.qq.com:465)

### Data Flow

1. RSS feeds → Parse with BeautifulSoup → Extract today's papers (title, link, abstract)
2. Filter by keywords → Group by matching keyword
3. Optional AI processing → 5-second delay between API calls
4. Generate HTML email → Send via SMTP

### GitHub Actions

Workflow: `.github/workflows/actions.yml`
- Triggers: Push to main, daily cron (UTC 23:00 / CST 7:00), manual watch
- Runs on: ubuntu-latest, Python 3.10
- Installs: requests, lxml, bs4, openai
- Passes secrets as environment variables to main.py

## Important Constraints

- Only processes papers published **today** (compares pubDate from RSS)
- Keywords are matched case-insensitively against paper **titles only**
- AI processing has a 5-second delay between calls to avoid rate limits
- Email is HTML-formatted with embedded CSS
- Uses QQ Mail SMTP (can be modified for other providers)
- Falls back to original English abstract if AI processing fails
