import requests
import feedparser
from datetime import datetime
from config import OLLAMA_URL, OLLAMA_MODEL, NICHE
import os

PEXELS_KEY = os.getenv("PEXELS_KEY")
IDEA_SOURCE = os.getenv("IDEA_SOURCE", "rss")

SKIP_KEYWORDS = ["election", "president", "minister",
                 "war", "killed", "attack", "trump", "politics"]

FEEDS = {
    "surreal": "https://www.thisiscolossal.com/feed",
    "landscape": "https://500px.com/editors.rss",
    "nature": "https://www.nationalgeographic.com/feed/rss",
    "space": "https://www.nasa.gov/rss/dyn/breaking_news.rss"
}


# ─── Source A: Pexels ─────────────────────────────────────────────────────────

def get_pexels_inspiration(niche: str) -> str:
    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": niche, "orientation": "portrait", "per_page": 5},
        timeout=15
    )
    resp.raise_for_status()
    photos = resp.json().get("photos", [])

    inspirations = []
    for p in photos:
        alt = p.get("alt", "")
        photographer = p.get("photographer", "")
        if alt:
            inspirations.append(f"{alt} (by {photographer})")

    result = " | ".join(inspirations)
    print(f"[Pexels] Inspiration: {result[:100]}...")
    return result


# ─── Source B: RSS ────────────────────────────────────────────────────────────

def get_latest_headlines(niche: str) -> str:
    feed_url = FEEDS.get(niche.lower())
    if not feed_url:
        for word in niche.lower().split():
            if word in FEEDS:
                feed_url = FEEDS[word]
                break
    feed_url = feed_url or FEEDS["surreal"]

    try:
        feed = feedparser.parse(feed_url)
        headlines = [
            e.title for e in feed.entries[:10]
            if not any(kw in e.title.lower() for kw in SKIP_KEYWORDS)
        ][:5]
        result = ", ".join(headlines)
        print(f"[RSS] Headlines: {result}")
        return result
    except Exception as e:
        print(f"[RSS] Failed: {e}")
        return "surreal nature, bioluminescent landscapes, dreamlike wilderness"


# ─── Main idea generator ──────────────────────────────────────────────────────

def generate_idea(niche: str = None) -> tuple[str, str]:
    niche = niche or NICHE

    # Pick source based on env variable
    if IDEA_SOURCE == "pexels":
        inspiration = get_pexels_inspiration(niche)
        source_label = "Pexels photo descriptions"
    else:
        inspiration = get_latest_headlines(niche)
        source_label = "RSS headlines"

    prompt = f"""You are a creative visual artist specialising in surreal, atmospheric AI-generated imagery.

{source_label}: {inspiration}

Using this as loose visual inspiration, generate a single vivid image prompt for an Instagram post about: {niche}

Rules:
- No text or words in the image
- Describe lighting, mood, composition, and style clearly
- Make it photorealistic and aesthetically striking
- Be inspired by the context but don't copy it literally — interpret the mood and atmosphere
- Output ONLY the image prompt, nothing else."""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=300
    )
    response.raise_for_status()
    idea = response.json()["response"].strip()
    print(f"[Idea] Generated: {idea[:80]}...")
    return idea, inspiration


if __name__ == "__main__":
    idea, inspiration = generate_idea()
    print(f"\nInspiration: {inspiration}")
    print(f"Idea: {idea}")
