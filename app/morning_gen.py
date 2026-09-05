from image_gen import generate_image
import sys
import requests
import os
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import textwrap
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
MORNING_BOT_TOKEN = os.getenv("MORNING_BOT_TOKEN")
MORNING_CHAT_ID = os.getenv("MORNING_CHAT_ID")
TELEGRAM_API = f"https://api.telegram.org/bot{MORNING_BOT_TOKEN}"

MORNING_WIDTH = int(os.getenv("MORNING_IMAGE_WIDTH", 1080))
MORNING_HEIGHT = int(os.getenv("MORNING_IMAGE_HEIGHT", 1080))

# Add your image_gen path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


SEASONS = {
    (12, 1, 2): "winter",
    (3, 4, 5): "spring",
    (6, 7, 8): "summer",
    (9, 10, 11): "autumn"
}

DAYS = ["Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"]

MORNING_QUOTES = [
    '"Every morning is a fresh beginning." — Unknown',
    '"Today is a good day to have a great day." — Unknown',
    '"Rise up, start fresh, see the bright opportunity in each new day." — Unknown',
    '"The secret of getting ahead is getting started." — Mark Twain',
    '"Believe you can and you\'re halfway there." — Theodore Roosevelt'
]

NEGATIVE_WORDS = ["violence", "death", "war", "fear",
                  "hate", "fail", "weak", "dark", "pain", "suffer"]


# Try these in order, fall back gracefully
FONT_OPTIONS = [
    "/System/Library/Fonts/Optima.ttc",           # elegant, classic
    "/System/Library/Fonts/Baskerville.ttc",       # serif, sophisticated
    "/System/Library/Fonts/GeezaPro.ttc",          # clean
    "/System/Library/Fonts/Helvetica.ttc",         # fallback
]


def get_season(month: int) -> str:
    for months, season in SEASONS.items():
        if month in months:
            return season
    return "summer"


def get_quote() -> str:
    try:
        resp = requests.get(
            "https://api.quotable.io/random",
            params={"tags": "inspirational|motivational|happiness|morning"},
            timeout=30,
            verify=False
        )
        data = resp.json()
        quote = f'"{data["content"]}" — {data["author"]}'
        if not any(word in quote.lower() for word in NEGATIVE_WORDS):
            return quote
    except Exception:
        pass
    return random.choice(MORNING_QUOTES)  # fallback


def generate_morning_style() -> str:
    prompt = """Generate a single cinematic landscape description for an AI image prompt.
Format: "[adjective] [location] at [time of day]"
Examples: "golden Sahara desert dunes at sunrise", "misty Japanese mountain peaks at dawn"
Return ONLY the description, nothing else. No quotes, no explanation."""

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=30
    )
    return resp.json().get(
        "response", "serene mountain valley at dawn").strip()


def generate_morning_prompt(target_date: datetime) -> tuple[str, str]:
    """Return an image prompt and quote for the next day's morning image."""
    day = DAYS[target_date.weekday()]
    season = get_season(target_date.month)
    date = target_date.strftime("%B %d")
    quote = get_quote()

    style_hint = generate_morning_style()

    prompt = f"""You are a creative visual artist specialising in warm, uplifting imagery.

Today is {day}, {date}. The current season is {season}.
Today's inspirational quote: {quote}

Generate a single vivid image prompt for a good morning image inspired by this quote and the current season/day.

Rules:
- Warm, uplifting, positive mood — no darkness, gloom, or melancholy
- No text or words in the image
- Think golden light, soft colours, nature, hope, energy
- {day} specific: {'energising and motivating' if target_date.weekday() < 4 else 'relaxed and joyful' if target_date.weekday() == 4 else 'warm and peaceful'}
- Describe lighting, mood, composition, and style clearly
- Style inspiration for today: {style_hint}
- Vary the setting dramatically each time — landscapes, seascapes, forests, deserts, mountains
- Output ONLY the image prompt, nothing else."""

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=300
    )
    resp.raise_for_status()
    image_prompt = resp.json()["response"].strip()
    print(f"[Morning] Quote: {quote}")
    print(f"[Morning] Prompt: {image_prompt[:80]}...")
    return image_prompt, quote


def send_to_telegram(image_path: str, quote: str):
    now = datetime.now()
    day = DAYS[now.weekday()]
    caption = f"🌅 *Good Morning!*\n\n_{quote}_\n\nHave a wonderful {day}! ✨"

    with open(image_path, "rb") as img:
        resp = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": MORNING_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown"
            },
            files={"photo": img}
        )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram send failed: {data}")
    print(f"[Morning] Sent to Telegram!")


def load_font(size: int) -> ImageFont:
    for path in FONT_OPTIONS:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def add_text_overlay(image_path: str, quote: str, day: str) -> str:
    img = Image.open(image_path).convert("RGBA")

    # ── Gradient overlay at bottom ────────────────────────────────
    gradient_height = int(img.height * 0.35)  # bottom 35%
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    for i in range(gradient_height):
        alpha = int(220 * (i / gradient_height))  # fades in from top
        y = img.height - gradient_height + i
        draw_overlay.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # ── Fonts ─────────────────────────────────────────────────────
    # Uses system fonts — no external dependencies
    try:
        size_scale = img.width / 1080
        font_quote = load_font(42)
        font_author = load_font(32)
        font_morning = load_font(int(52 * size_scale))
    except Exception:
        font_quote = ImageFont.load_default()
        font_author = ImageFont.load_default()
        font_morning = ImageFont.load_default()

    # ── Parse quote and author ─────────────────────────────────────
    # Quote format: '"text" — Author'
    if "—" in quote:
        parts = quote.split("—", 1)
        quote_text = parts[0].strip().strip('"')
        author = f"— {parts[1].strip()}"
    else:
        quote_text = quote.strip().strip('"')
        author = ""

    # ── Wrap quote text ───────────────────────────────────────────
    max_chars = 45  # characters per line
    wrapped = textwrap.wrap(quote_text, width=max_chars)
    line_height = 52
    padding = 40

    # Calculate starting Y position
    total_text_height = (len(wrapped) * line_height) + \
        60 + 50  # lines + author + morning
    start_y = img.height - total_text_height - padding

    # ── Draw quote lines ──────────────────────────────────────────
    y = start_y
    for i, line in enumerate(wrapped):
        if i == 0:
            text = f'"{line}'
        elif i == len(wrapped) - 1:
            text = f'{line}"'
        else:
            text = line
        draw.text((padding, y), text, font=font_quote, fill="white",
                  stroke_width=1, stroke_fill=(0, 0, 0, 180))
        y += line_height

    # Last line gets closing quote
    # ── Draw author ───────────────────────────────────────────────
    if author:
        draw.text((padding, y + 8), author,
                  font=font_author, fill=(200, 200, 200, 255),
                  stroke_width=1, stroke_fill=(0, 0, 0, 180))
        y += 50

    # ── Draw Good Morning line ────────────────────────────────────
    morning_text = f"Good Morning — {day}"
    draw.text((padding, y + 20), morning_text,
              font=font_morning, fill=(255, 215, 0, 255),  # gold
              stroke_width=1, stroke_fill=(0, 0, 0, 200))

    # ── Save ──────────────────────────────────────────────────────
    output_path = image_path.replace(".png", "_morning.png")
    img.convert("RGB").save(output_path, quality=95)
    print(f"[Morning] Text overlay added: {output_path}")
    return output_path


def run_morning_pipeline():
    print(f"\n{'='*50}")
    print(f"[Morning] Starting morning image pipeline...")
    print(f"{'='*50}\n")

    # Prepare tomorrow's image and keep its date consistent across the prompt and overlay.
    os.environ["IMAGE_WIDTH"] = os.getenv("MORNING_IMAGE_WIDTH", "1080")
    os.environ["IMAGE_HEIGHT"] = os.getenv("MORNING_IMAGE_HEIGHT", "1080")

    target_date = datetime.now() + timedelta(days=1)
    image_prompt, quote = generate_morning_prompt(target_date)
    image_path = generate_image(image_prompt)
    image_path = add_text_overlay(
        image_path, quote, DAYS[target_date.weekday()])
    send_to_telegram(image_path, quote)

    print(f"[Morning] Done! 🌅")


if __name__ == "__main__":
    run_morning_pipeline()
