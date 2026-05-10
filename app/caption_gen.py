import requests
from config import OLLAMA_URL, OLLAMA_MODEL


def generate_caption(prompt: str, niche: str) -> str:
    system_prompt = f"""You are an Instagram copywriter for an AI art account in the {niche} niche.
Given an image description, write an Instagram caption.

Rules:
- 2-3 sentences max, punchy and evocative
- Add 5-8 relevant hashtags at the end on a new line
- No generic phrases like "check this out" or "amazing content"
- Tone: thoughtful, aesthetic, slightly poetic
- Output ONLY the caption + hashtags. Nothing else."""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": f"{system_prompt}\n\nImage description: {prompt}",
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    caption = response.json()["response"].strip()
    print(f"[Caption] Generated: {caption[:80]}...")
    return caption


if __name__ == "__main__":
    test_prompt = "A minimalist concrete building at golden hour, soft shadows, cinematic"
    print(generate_caption(test_prompt, "minimalist architecture"))
