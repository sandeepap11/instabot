import requests
import feedparser
from config import OLLAMA_URL, OLLAMA_MODEL, NICHE
import os
import random
from db import get_conn, _mark_seen, _get_seen_ids

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

PEXELS_QUERIES = [
    "desert sunrise", "ocean waves dramatic", "mountain peaks clouds",
    "arctic landscape", "volcanic landscape", "canyon dramatic light",
    "tropical storm sky", "glacier ice blue", "savanna golden hour",
    "coral reef underwater", "misty forest", "night sky milky way",
    "bioluminescent waves", "lightning storm desert", "aurora borealis",
    "salt flats reflection", "lava flow night", "sand dunes shadow",
    "waterfall jungle", "ice cave blue light", "rainforest canopy mist",
]


# ─── Source A: Pexels ─────────────────────────────────────────────────────────

def get_pexels_inspiration() -> tuple[str, str]:
    query = random.choice(PEXELS_QUERIES)

    # random page within a reasonable range to avoid always hitting top results
    page = random.randint(1, 5)

    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "orientation": "portrait",
                "per_page": 15, "page": page},
        timeout=15
    )
    resp.raise_for_status()
    photos = resp.json().get("photos", [])

    if not photos:
        print(f"[Pexels] Query: {query} | No photos found on page {page}")
        return "", query

    with get_conn() as conn:
        seen_ids = _get_seen_ids(conn)

        # filter out photos we've already used as inspiration
        unseen_photos = [p for p in photos if p.get("id") not in seen_ids]

        # fallback: if everything on this page was already seen, just use the full page
        pool = unseen_photos if unseen_photos else photos

        # pick a random subset (not just the top N) to build inspiration from
        sample_size = min(5, len(pool))
        sampled = random.sample(pool, sample_size)

        inspirations = []
        for p in sampled:
            alt = p.get("alt", "")
            photographer = p.get("photographer", "")
            if alt:
                inspirations.append(f"{alt} (by {photographer})")
            _mark_seen(conn, p.get("id"), query)

    result = " | ".join(inspirations)
    print(
        f"[Pexels] Query: {query} | Page: {page} | Inspiration: {result[:80]}...")
    return result, query


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

    if IDEA_SOURCE == "pexels":
        inspiration, query = get_pexels_inspiration()
        source_label = "Pexels photo descriptions"
        environment_hint = f"\n- Today's environment must be: {query} — avoid forests and trees unless specifically relevant"
    else:
        inspiration = get_latest_headlines(niche)
        source_label = "RSS headlines"
        environment_hint = ""  # no constraint for RSS

    prompt = f"""You are a creative visual artist...

{source_label}: {inspiration}

Rules:
- No text or words in the image
- Describe lighting, mood, composition, and style clearly
- Make it photorealistic and aesthetically striking
- Be inspired by the context but don't copy it literally {environment_hint}
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
