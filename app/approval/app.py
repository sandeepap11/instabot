from db import get_conn, mark_posted
from ngrok_host import get_public_image_url, start_image_server, start_tunnel
from instagram import post_image, check_token_validity
from db import get_pending_posts, get_published_posts, get_rejected_posts, get_all_posts, update_status
from flask import Flask, render_template, redirect, url_for, flash
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


app = Flask(__name__)
app.secret_key = "instabot-local-secret"


@app.route("/favicon.png")
def favicon():
    from flask import send_from_directory
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    return send_from_directory(template_dir, "favicon.png", mimetype="image/png")


# Start image server + ngrok tunnel when Flask starts
start_image_server(port=5001)
start_tunnel(port=5001)


@app.route("/")
@app.route("/review")
def review():
    posts = get_pending_posts()
    return render_template("review.html", posts=posts, section="pending")


@app.route("/published")
def published_view():
    posts = get_published_posts()
    return render_template("review.html", posts=posts, section="published")


@app.route("/rejected")
def rejected_view():
    posts = get_rejected_posts()
    return render_template("review.html", posts=posts, section="rejected")


@app.route("/history")
def history():
    posts = get_all_posts()
    return render_template("review.html", posts=posts, section="history")


@app.route("/approve/<post_id>")
def approve(post_id):
    update_status(post_id, "approved")
    flash(f"✅ Post approved and queued for posting.", "success")
    return redirect(url_for("review"))


@app.route("/reject/<post_id>")
def reject(post_id):
    update_status(post_id, "rejected")
    flash(f"🗑 Post rejected.", "info")
    return redirect(url_for("review"))


@app.route("/post-now/<post_id>")
def post_now(post_id):
    """Approve + immediately post to Instagram."""
    from db import get_conn
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?",
                           (post_id,)).fetchone()

    if not row:
        flash("Post not found.", "error")
        return redirect(url_for("review"))

    try:
        public_url = get_public_image_url(row["image_path"])
        post_image(public_url, row["caption"])
        mark_posted(post_id)
        flash("🚀 Posted to Instagram!", "success")
    except Exception as e:
        flash(f"❌ Failed to post: {str(e)}", "error")

    return redirect(url_for("review"))


@app.route("/check-token")
def check_token():
    valid = check_token_validity()
    if valid:
        flash("✅ Instagram token is valid.", "success")
    else:
        flash("❌ Instagram token is invalid or expired. Update your .env.", "error")
    return redirect(url_for("review"))


@app.route("/unapprove/<post_id>")
def unapprove(post_id):
    update_status(post_id, "pending")
    flash("↩️ Post moved back to pending.", "info")
    return redirect(url_for("review"))


@app.route("/details/<post_id>")
def details(post_id):
    with get_conn() as conn:
        post = conn.execute(
            "SELECT * FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
    return render_template("details.html", post=dict(post))


if __name__ == "__main__":
    app.run(port=5000, debug=False)
