import requests
from config import IG_USER_ID, IG_ACCESS_TOKEN

GRAPH_URL = "https://graph.facebook.com/v19.0"


def _check_config():
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        raise RuntimeError(
            "IG_USER_ID and IG_ACCESS_TOKEN must be set in .env. "
            "See readme.md for how to get these."
        )


def create_media_container(image_url: str, caption: str) -> str:
    """Step 1: Upload image URL + caption to Instagram. Returns container ID."""
    _check_config()
    resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN
        }
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Instagram API error: {data['error']['message']}")

    container_id = data["id"]
    print(f"[Instagram] Media container created: {container_id}")
    return container_id


def publish_container(container_id: str) -> str:
    """Step 2: Publish the container. Returns the post ID."""
    _check_config()
    resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": IG_ACCESS_TOKEN
        },
        timeout=100
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(
            f"Instagram publish error: {data['error']['message']}")

    post_id = data["id"]
    print(f"[Instagram] Published! Post ID: {post_id}")
    return post_id


def post_image(image_url: str, caption: str) -> str:
    """Full flow: container → publish. Returns post ID."""
    container_id = create_media_container(image_url, caption)
    post_id = publish_container(container_id)
    return post_id


def check_token_validity() -> bool:
    """Quick sanity check that your token is still valid."""
    _check_config()
    resp = requests.get(
        f"{GRAPH_URL}/me",
        params={"access_token": IG_ACCESS_TOKEN}
    )
    data = resp.json()
    if "error" in data:
        print(f"[Instagram] Token invalid: {data['error']['message']}")
        return False
    print(
        f"[Instagram] Token valid. Account: {data.get('name', data.get('id'))}")
    return True


if __name__ == "__main__":
    check_token_validity()
