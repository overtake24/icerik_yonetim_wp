from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from modules.ui_module import handle_form_submission
from modules.wordpress_module import WordpressClient
from modules.image_module import fetch_multiple_images
from modules.translation_manager import TranslationManager
from modules.template_manager import TemplateManager
from modules.history_manager import HistoryManager

load_dotenv("config.env")

app = Flask(__name__)

wp_client = WordpressClient(
    url=os.getenv("WP_URL"),
    username=os.getenv("WP_USER"),
    password=os.getenv("WP_APP_PASSWORD")
)

template_manager = TemplateManager()
history_manager = HistoryManager()
translation_manager = TranslationManager()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        result = handle_form_submission(request.form, wp_client)
        return jsonify(result)

    # GET isteği için template ve geçmiş verileri hazırla
    templates = template_manager.get_templates()
    history = history_manager.get_posts_history()
    stats = history_manager.get_post_stats()

    return render_template('index.html',
                           templates=templates,
                           history=history,
                           stats=stats,
                           wp_url=os.getenv("WP_URL"))


@app.route("/fetch_images")
def fetch_images():
    keywords = request.args.get("keywords", "")
    source = request.args.get("source", "pexels")

    if not keywords:
        return jsonify({"image_urls": []})

    image_urls = fetch_multiple_images(keywords, count=8, source=source)
    return jsonify({"image_urls": image_urls})


@app.route("/translate_keywords")
def translate_keywords():
    keywords = request.args.get("keywords", "")
    if not keywords:
        return jsonify({"translated": ""})

    translated = translation_manager.translate_to_english(keywords)
    return jsonify({"translated": translated})


@app.route('/save_template', methods=['POST'])
def save_template():
    try:
        data = request.get_json()
        template_manager.save_template(data['name'], data['content'])
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)