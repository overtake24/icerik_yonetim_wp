from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
from modules.ui_module import handle_form_submission
from modules.wordpress_module import WordpressClient
from modules.image_module import fetch_image_url, fetch_multiple_images

load_dotenv("config.env")

app = Flask(__name__)

wp_client = WordpressClient(
    url=os.getenv("WP_URL"),
    username=os.getenv("WP_USER"),
    password=os.getenv("WP_APP_PASSWORD")
)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    if request.method == 'POST':
        form_data = request.form
        message = handle_form_submission(form_data, wp_client)
    return render_template('index.html', message=message)

@app.route("/fetch_image")
def fetch_image():
    keywords = request.args.get("keywords", "")
    source = request.args.get("source", "pexels")

    image_url = fetch_image_url(keywords, source)
    return {"image_url": image_url}

if __name__ == '__main__':
    app.run(debug=True)