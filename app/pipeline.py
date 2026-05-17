from idea_gen import generate_idea
from caption_gen import generate_caption
from image_gen import generate_image
from db import save_post, init_db
from config import NICHE
from telegram_notify import send_approval_notification


def run_daily_pipeline(niche: str = None):
    """
    Runs once a day:
    1. Generate idea (Ollama)
    2. Generate image (ComfyUI)
    3. Generate caption (Ollama)
    4. Save to DB as 'pending' — waits for your approval in the Flask UI
    """
    niche = niche or NICHE
    print(f"\n{'='*50}")
    print(f"[Pipeline] Starting daily pipeline for niche: {niche}")
    print(f"{'='*50}\n")

    init_db()

    # Step 1: Generate idea/prompt
    print("[Pipeline] Step 1/3 — Generating idea...")
    idea = generate_idea(niche)

    # Step 2: Generate image from idea
    print("[Pipeline] Step 2/3 — Generating image...")
    image_path = generate_image(idea)

    # Step 3: Generate caption from idea
    print("[Pipeline] Step 3/3 — Generating caption...")
    caption = generate_caption(idea, niche)

    # Step 4: Save to DB, status = pending
    post_id = save_post(niche, idea, caption, image_path)
    send_approval_notification(post_id, image_path, idea, caption)

    print(f"\n[Pipeline] Done! Post {post_id} is waiting for your approval.")
    print("[Pipeline] Open http://localhost:5000/review to approve or reject.\n")

    return post_id


if __name__ == "__main__":
    run_daily_pipeline()
