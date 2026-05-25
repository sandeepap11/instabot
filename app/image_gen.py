import json
import uuid
import os
import urllib.request
import urllib.error
import websocket
import requests
from datetime import datetime
from config import COMFY_URL, IMAGES_DIR
import random


# ─── Minimal default workflow (text-to-image with SDXL-style nodes) ───────────
# If you have a saved workflow JSON from ComfyUI, export it via
# "Save (API format)" and replace this with: json.load(open("my_workflow.json"))

import json


def build_workflow(prompt: str) -> dict:
    base = os.path.dirname(os.path.abspath(__file__))
    workflow_path = os.path.join(base, "config", "workflow_api.json")

    with open(workflow_path) as f:
        workflow = json.load(f)

    workflow["6"]["inputs"]["text"] = prompt
    # temporarily add this line after the injection
    print(f"[DEBUG] Prompt injected: {workflow['6']['inputs']['text']}")
    workflow["3"]["inputs"]["seed"] = random.randint(0, 2**32)
    workflow["5"]["inputs"]["width"] = int(os.getenv("IMAGE_WIDTH", 1024))
    workflow["5"]["inputs"]["height"] = int(os.getenv("IMAGE_HEIGHT", 1024))
    return workflow


def queue_prompt(workflow: dict, client_id: str) -> str:
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=payload)
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["prompt_id"]


def wait_for_completion(client_id: str, prompt_id: str):
    ws = websocket.WebSocket()
    ws.connect(
        f"ws://{COMFY_URL.replace('http://', '')}/ws?clientId={client_id}")
    print("[ComfyUI] Waiting for image generation...")

    try:
        while True:
            raw = ws.recv()
            if isinstance(raw, bytes):
                continue  # binary preview frames, skip
            msg = json.loads(raw)
            if msg["type"] == "executing":
                data = msg["data"]
                if data.get("node") is None and data.get("prompt_id") == prompt_id:
                    print("[ComfyUI] Generation complete.")
                    break
    finally:
        ws.close()


def fetch_image(prompt_id: str) -> bytes:
    history_url = f"{COMFY_URL}/history/{prompt_id}"
    resp = requests.get(history_url)
    resp.raise_for_status()
    history = resp.json()

    outputs = history[prompt_id]["outputs"]
    # Get the first image from any output node
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            img_info = node_output["images"][0]
            img_url = (
                f"{COMFY_URL}/view"
                f"?filename={img_info['filename']}"
                f"&subfolder={img_info.get('subfolder', '')}"
                f"&type={img_info.get('type', 'output')}"
            )
            img_resp = requests.get(img_url)
            img_resp.raise_for_status()
            return img_resp.content

    raise RuntimeError("No image found in ComfyUI output.")


def generate_image(prompt: str) -> str:
    """
    Full pipeline: queue → wait → fetch → save locally.
    Returns the local file path of the saved image.
    """
    client_id = str(uuid.uuid4())
    workflow = build_workflow(prompt)

    print(f"[ComfyUI] Queuing prompt...")
    prompt_id = queue_prompt(workflow, client_id)

    wait_for_completion(client_id, prompt_id)

    image_bytes = fetch_image(prompt_id)

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_id[:8]}.png"
    filepath = os.path.join(IMAGES_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    print(f"[ComfyUI] Image saved: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate_image(
        "A minimalist concrete building at golden hour, cinematic lighting")
    print(f"Saved to: {path}")
