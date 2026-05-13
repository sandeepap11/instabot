"""
scheduler.py — runs both jobs on a daily schedule:
  - GENERATE_TIME : runs the pipeline (idea → image → caption → DB)
  - POST_TIME     : posts any approved posts to Instagram

Run this once and leave it: `python scheduler.py`
Keep it alive with a terminal session, or use launchd/screen for persistence.
"""

import threading
import time
import schedule
from config import GENERATE_TIME, POST_TIME
from db import init_db, get_approved_posts, mark_posted
from pipeline import run_daily_pipeline
from instagram import post_image
from ngrok_host import get_public_image_url, start_image_server, start_tunnel
import sys
import os

import subprocess

# Make sure imports work from root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def job_generate():
    """Runs daily at GENERATE_TIME. Generates content and saves as pending."""
    print(f"\n[Scheduler] Running generation job...")
    try:
        run_daily_pipeline()
    except Exception as e:
        print(f"[Scheduler] Generation failed: {e}")


def job_post():
    """Runs daily at POST_TIME. Posts any approved posts to Instagram."""
    print(f"\n[Scheduler] Running post job...")
    approved = get_approved_posts()

    if not approved:
        print("[Scheduler] No approved posts to publish.")
        return

    for post in approved:
        try:
            public_url = get_public_image_url(post["image_path"])
            post_image(public_url, post["caption"])
            mark_posted(post["id"])
            print(f"[Scheduler] Posted: {post['id']}")
        except Exception as e:
            print(f"[Scheduler] Failed to post {post['id']}: {e}")


def start_approval_ui():
    """Starts the Flask approval UI in a background thread."""
    from approval.app import app
    thread = threading.Thread(
        target=lambda: app.run(port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    thread.start()
    print("[Scheduler] Approval UI running at http://localhost:5000/review")


if __name__ == "__main__":
    # Kill any zombie processes on our ports before starting
    subprocess.run("lsof -ti:5001 | xargs kill -9",
                   shell=True, capture_output=True)
    subprocess.run("lsof -ti:5000 | xargs kill -9",
                   shell=True, capture_output=True)
    print("=" * 50)
    print("  InstaBot Scheduler Starting")
    print("=" * 50)

    init_db()

    # Start image server + ngrok tunnel (needed for approval UI previews + posting)
    start_image_server(port=5001)
    start_tunnel(port=5001)

    # Start approval UI
    start_approval_ui()

    # Schedule jobs
    schedule.every().day.at(GENERATE_TIME).do(job_generate)
    schedule.every().day.at(POST_TIME).do(job_post)

    print(f"\n[Scheduler] Generation job scheduled at {GENERATE_TIME}")
    print(f"[Scheduler] Posting job scheduled at {POST_TIME}")
    print(f"[Scheduler] Approval UI: http://localhost:5000/review")
    print(f"[Scheduler] Running... (Ctrl+C to stop)\n")

    # Keep alive
    while True:
        schedule.run_pending()
        time.sleep(30)
