import requests
import feedparser
from datetime import datetime
from config import OLLAMA_URL, OLLAMA_MODEL, NICHE

# Add your niche → RSS feed mappings here
# FEEDS = {
#     "architecture": "https://www.archdaily.com/feed",
#     "nature": "https://feeds.nationalgeographic.com/ng/photography/photo-of-the-day",
#     "technology": "https://feeds.wired.com/wired/index",
#     "fashion": "https://www.vogue.com/feed/rss",
#     "travel": "https://www.lonelyplanet.com/news/feed",
#     "art": "https://www.thisiscolossal.com/feed",
#     "general": "https://feeds.bbci.co.uk/news/rss.xml"
# }

FEEDS = {
    "surreal": "https://www.thisiscolossal.com/feed",        # art/design
    "landscape": "https://500px.com/editors.rss",             # photography
    "nature": "https://www.nationalgeographic.com/feed/rss",  # nat geo
    "space": "https://www.nasa.gov/rss/dyn/breaking_news.rss"  # NASA
}

SKIP_KEYWORDS = ["election", "president", "minister",
                 "war", "killed", "attack", "trump", "politics"]


def get_latest_headlines(niche: str) -> str:
    # try exact match first, then try each word
    feed_url = FEEDS.get(niche.lower())
    if not feed_url:
        for word in niche.lower().split():
            if word in FEEDS:
                feed_url = FEEDS[word]
                break
    feed_url = feed_url or FEEDS["surreal"]  # final fallback

    try:
        feed = feedparser.parse(feed_url)
        # headlines = [e.title for e in feed.entries[:5]]
        headlines = [
            e.title for e in feed.entries[:10]
            if not any(kw in e.title.lower() for kw in SKIP_KEYWORDS)
        ][:5]  # take top 5 after filtering
        if not headlines:
            return "no headlines found"
        return ", ".join(headlines)
    except Exception as e:
        print(f"[RSS] Failed to fetch feed: {e}")
        return "no headlines found"


def generate_idea(niche: str = None) -> str:
    niche = niche or NICHE
    headlines = get_latest_headlines(niche)

    print(f"[RSS] Headlines: {headlines}")

    prompt = f"""You are a creative Instagram content strategist specialising in AI-generated imagery.
Today is {datetime.now().strftime('%B %Y')}.

Latest developments in {niche}: {headlines}

Use these ONLY as loose atmospheric inspiration — not literally.
Extract the mood, colour palette, or emotion. Do NOT include people, 
events, or narrative elements from the headlines.
Output ONLY the image prompt.

Rules:
- No text or words in the image
- Describe lighting, mood, composition, and style clearly
- Make it photorealistic and aesthetically striking
- Be inspired by the current context but don't be too literal
- Output ONLY the image prompt, nothing else."""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    idea = response.json()["response"].strip()
    print(f"[Idea] Generated: {idea[:80]}...")
    return idea, headlines


if __name__ == "__main__":
    print(generate_idea())
