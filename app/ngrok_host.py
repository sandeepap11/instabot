import threading
from pyngrok import ngrok
from flask import Flask, send_from_directory
from config import NGROK_AUTHTOKEN, IMAGES_DIR

# Separate Flask app just for serving images (not the approval UI)
image_server = Flask(__name__)
_tunnel_url = None


@image_server.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


def start_image_server(port: int = 5001):
    """Starts the image file server in a background thread."""
    thread = threading.Thread(
        target=lambda: image_server.run(
            port=port, debug=False, use_reloader=False),
        daemon=True
    )
    thread.start()
    print(f"[ngrok] Image server running on port {port}")


def start_tunnel(port: int = 5001) -> str:
    """Opens an ngrok tunnel and returns the public base URL."""
    global _tunnel_url
    if _tunnel_url:
        return _tunnel_url  # already running

    ngrok.set_auth_token(NGROK_AUTHTOKEN)
    tunnel = ngrok.connect(port)
    _tunnel_url = tunnel.public_url
    print(f"[ngrok] Tunnel open: {_tunnel_url}")
    return _tunnel_url


def get_public_image_url(image_path: str) -> str:
    """
    Given a local image path, returns a publicly accessible URL via ngrok.
    Instagram Graph API needs a public URL to pull the image from.
    """
    import os
    filename = os.path.basename(image_path)
    base_url = start_tunnel()
    return f"{base_url}/images/{filename}"


def stop_tunnel():
    ngrok.kill()
    print("[ngrok] Tunnel closed.")


if __name__ == "__main__":
    start_image_server()
    url = start_tunnel()
    print(f"Test URL: {url}/images/test.png")
    input("Press Enter to stop...")
    stop_tunnel()
