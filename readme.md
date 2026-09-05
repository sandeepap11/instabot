# InstaBot — AI Instagram Pipeline

InstaBot is a local AI-powered Instagram content pipeline that runs entirely on your machine. It scrapes trending headlines from niche RSS feeds, uses a local LLM (Qwen3 via Ollama) to generate atmospheric image prompts inspired by those headlines, and passes them to ComfyUI to generate stunning AI images. Each post goes through a human approval step via a clean local web UI before anything reaches Instagram — so you stay in control. You will also get the image on Telegram to approve / post / reject. Approved posts are served via an ngrok tunnel and published directly to Instagram through the Graph API. The whole pipeline runs on a daily schedule, giving you a hands-off content machine that still keeps you in the loop.

Stack: Python · Ollama (Qwen3) · ComfyUI (DreamShaper XL) · Flask · SQLite · ngrok · Instagram Graph API · Telegram

# Quick start

## Virtual Environment

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Run Ollama

ollama serve

## Run Comfy ui

cd ~/ComfyUI
python main.py --force-fp16 --lowvram

## Run app

python app/scheduler.py

# Kill processes if access denied error on browser and retry

lsof -ti:5001 | xargs kill -9

--

# Run pipeline (only for Image generation on demand)

python app/pipeline.py

---

## Morning Images

The scheduled morning job generates the image and inspirational quote for the
following day. It sends the completed image to Telegram with the next day's
weekday shown in the overlay.

## Folder Structure

```
instabot
├──app/
    ├── config.py              # All config in one place
    ├── db.py                  # SQLite DB setup + queries
    ├── idea_gen.py            # Ollama prompt generation
    ├── image_gen.py           # ComfyUI image generation
    ├── caption_gen.py         # Ollama caption generation
    ├── instagram.py           # Instagram Graph API posting
    ├── ngrok_host.py          # ngrok tunnel for image hosting
    ├── pipeline.py            # Daily pipeline (orchestrator)
    ├── approval/
    │   ├── app.py             # Flask approval UI
    │   └── templates/
    │       └── review.html    # Approval UI template
    ├── scheduler.py           # Runs the daily cron jobs
├── requirements.txt
└── .env                   # Your secrets (never commit this)
```

## Setup

python3 -m venv venv
source venv/bin/activate

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your values
3. Make sure Ollama is running: `ollama serve`
4. Make sure ComfyUI is running on port 8188
5. Run: `python3 scheduler.py`
6. Open approval UI: `http://localhost:5000/review`

## Instagram Graph API Setup

1. Go to developers.facebook.com
2. Create an app → Add Instagram Graph API product
3. Link a Professional/Creator Instagram account
4. Generate a long-lived access token
5. Paste into .env

## ngrok Setup

1. `brew install ngrok`
2. Sign up at ngrok.com (free tier is fine)
3. `ngrok config add-authtoken YOUR_TOKEN`
4. The app starts ngrok automatically

# Comfy UI Set up

## Step 1 — Install ComfyUI

cd ~
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install torch torchvision torchaudio (M1/M2/M3)
pip install -r requirements.txt

## Step 2 — Get a Model Checkpoint

ComfyUI needs at least one model to generate images. Easiest option:

Go to civitai.com or huggingface.co
Download a checkpoint — good starting points:

Realistic Vision V6 — photorealistic, good for lifestyle/fashion content
DreamShaper XL — versatile, handles most niches well
SDXL Base 1.0 — solid all-rounder from Stability AI

Drop the .safetensors file into:
ComfyUI/models/checkpoints/

Then update your .env:

# whatever filename you downloaded

COMFY_CHECKPOINT=realisticVisionV60B1_v51VAE.safetensors

And update image_gen.py line in build_workflow():
python"ckpt_name": os.getenv("COMFY_CHECKPOINT", "your_model.safetensors")

## Step 3 — Start ComfyUI

cd ~/ComfyUI
python main.py --force-fp16

It'll start at http://localhost:8188 — open that in your browser to confirm it's running and you can see the default workflow.

## Step 4 — Export Your Workflow as API Format

This is the bit that connects to our image_gen.py. In the ComfyUI browser UI:

Load your workflow (or use the default one)
Click the gear icon (Settings) in the top right
Enable "Dev Mode Options"
You'll now see a "Save (API Format)" button
Click it — saves a workflow_api.json

## Step 5 — Quick Test

Once ComfyUI is running, test the image gen module directly:

cd instabot
python image_gen.py

Should generate an image and save it to instabot/generated_images/. If you see the file appear, you're good.

Most common issue on Mac — if it's slow or crashing, it's likely a memory thing. Add --lowvram flag:

python3 main.py --force-fp16 --lowvram

# RANDOM FIXES

/Applications/Python\ 3.13/Install\ Certificates.command
