import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_approval_notification(post_id: str, image_path: str, prompt: str, caption: str):
    """
    Sends the generated image to Telegram with Approve / Reject inline buttons.
    """
    # Send the image
    with open(image_path, "rb") as img:
        resp = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": f"...",
                "parse_mode": "Markdown",
                "reply_markup": json.dumps({   # ← wrap in json.dumps()
                    "inline_keyboard": [[
                        {"text": "✅ Approve", "callback_data": f"approve:{post_id}"},
                        {"text": "🚀 Post Now", "callback_data": f"postnow:{post_id}"},
                        {"text": "❌ Reject",  "callback_data": f"reject:{post_id}"}
                    ]]
                })
            },
            files={"photo": img}
        )

    resp_data = resp.json()
    if not resp_data.get("ok"):
        raise RuntimeError(f"Telegram send failed: {resp_data}")

    print(f"[Telegram] Notification sent for post {post_id}")
    return resp_data


def start_callback_listener():
    """
    Long-polls Telegram for button presses and updates DB accordingly.
    Runs in a background thread.
    """
    import threading
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from db import update_status, mark_posted, get_conn
    from instagram import post_image
    from ngrok_host import get_public_image_url

    def listen():
        offset = None
        print("[Telegram] Listening for button presses...")

        while True:
            try:
                params = {"timeout": 30, "allowed_updates": ["callback_query"]}
                if offset:
                    params["offset"] = offset

                resp = requests.get(
                    f"{TELEGRAM_API}/getUpdates", params=params, timeout=35)
                updates = resp.json().get("result", [])

                for update in updates:
                    offset = update["update_id"] + 1
                    callback = update.get("callback_query")
                    if not callback:
                        continue

                    data = callback["data"]          # e.g. "approve:uuid"
                    call_id = callback["id"]
                    action, post_id = data.split(":", 1)

                    if action == "approve":
                        update_status(post_id, "approved")
                        answer_text = "✅ Approved! Will post at scheduled time."

                    elif action == "postnow":
                        with get_conn() as conn:
                            row = conn.execute(
                                "SELECT * FROM posts WHERE id = ?", (post_id,)
                            ).fetchone()
                        if row:
                            try:
                                public_url = get_public_image_url(
                                    row["image_path"])
                                post_image(public_url, row["caption"])
                                mark_posted(post_id)
                                answer_text = "🚀 Posted to Instagram!"
                            except Exception as e:
                                answer_text = f"❌ Post failed: {str(e)}"
                        else:
                            answer_text = "❌ Post not found."

                    elif action == "reject":
                        update_status(post_id, "rejected")
                        answer_text = "❌ Rejected."

                    else:
                        answer_text = "Unknown action."

                   # Answer the callback so button stops spinning
                    requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={
                        "callback_query_id": call_id,
                        "text": answer_text,
                        "show_alert": False
                    })

                    # Edit the message to remove buttons and show result
                    requests.post(f"{TELEGRAM_API}/editMessageCaption", json={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "message_id": callback["message"]["message_id"],
                        "caption": answer_text,
                        "parse_mode": "Markdown"
                    })

                    print(f"[Telegram] {action} → post {post_id}")

            except Exception as e:
                print(f"[Telegram] Listener error: {e}")

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()


if __name__ == "__main__":
    # Quick test — sends a test message to confirm setup is working
    resp = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "✅ Instabot Telegram notifications are working!"
        }
    )
    print(resp.json())
