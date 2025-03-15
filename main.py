from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import json
import requests
from io import BytesIO
from PIL import Image
# Güncellenmiş UI modülünü kullan
from modules.ui_module import handle_form_submission
from modules.wordpress_module import WordpressClient
from modules.image_module import fetch_multiple_images, fetch_and_resize_image
from modules.translation_manager import TranslationManager
from modules.template_manager import TemplateManager
from modules.history_manager import HistoryManager

load_dotenv("config.env")

app = Flask(__name__)

# Static klasörü oluştur
os.makedirs("static/images", exist_ok=True)

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
        # Formdan gelen verileri işle
        form_data = request.form.to_dict()

        # Etiketleri kontrol et ve boşsa anahtar kelimeleri kullan
        if not form_data.get('tags'):
            form_data['tags'] = form_data.get('keywords', '')

        # İçerik görselleri
        if 'content_images' in form_data:
            try:
                # JSON olarak parse et
                form_data['content_images'] = json.loads(form_data['content_images'])
            except Exception as e:
                print(f"İçerik görselleri parse hatası: {e}")
                # JSON parse edilemezse, virgülle ayrılmış URL listesi olarak kabul et
                content_images = form_data.get('content_images', '')
                if isinstance(content_images, str) and ',' in content_images:
                    form_data['content_images'] = content_images.split(',')
                elif isinstance(content_images, str) and content_images.strip():
                    form_data['content_images'] = [content_images]
                else:
                    form_data['content_images'] = []

        result = handle_form_submission(form_data, wp_client)
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
    min_width = int(request.args.get("min_width", 800))
    min_height = int(request.args.get("min_height", 600))

    # Çevrilmiş anahtar kelimeleri de al
    translated_keywords = request.args.get("translated_keywords", "")

    if not keywords:
        return jsonify({"image_urls": [], "image_sizes": []})

    # Önce çevrilmiş anahtar kelimeleri kullan, yoksa orijinali kullan
    search_keywords = translated_keywords if translated_keywords else keywords
    print(f"Görsel araması: {search_keywords}")

    # Boyut bilgisini de döndür
    image_urls, image_sizes = fetch_multiple_images(
        search_keywords,
        count=8,
        source=source,
        min_width=min_width,
        min_height=min_height
    )

    # Eğer sonuç yoksa ve çevrilmiş kelimeler kullanıldıysa, orijinal kelimelerle tekrar dene
    if not image_urls and translated_keywords and translated_keywords != keywords:
        print(f"Çevrilmiş kelimelerle sonuç bulunamadı, orijinal kelimelerle tekrar deneniyor: {keywords}")
        image_urls, image_sizes = fetch_multiple_images(
            keywords,
            count=8,
            source=source,
            min_width=min_width,
            min_height=min_height
        )

    return jsonify({"image_urls": image_urls, "image_sizes": image_sizes})


@app.route("/translate_keywords")
def translate_keywords():
    keywords = request.args.get("keywords", "")
    if not keywords:
        return jsonify({"translated": ""})

    try:
        translated = translation_manager.translate_to_english(keywords)
        print(f"Çeviri sonucu: {keywords} -> {translated}")
        return jsonify({"translated": translated})
    except Exception as e:
        print(f"Çeviri API hatası: {e}")
        # Hata durumunda orijinal kelimeyi döndür
        return jsonify({"translated": keywords, "error": str(e)})


@app.route('/save_template', methods=['POST'])
def save_template():
    try:
        data = request.get_json()
        template_manager.save_template(data['name'], data['content'])
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/resize_image', methods=['POST'])
def resize_image():
    try:
        data = request.get_json()
        image_url = data.get('image_url')
        width = int(data.get('width', 800))
        height = int(data.get('height', 600))
        maintain_aspect = data.get('maintain_aspect', True)

        if not image_url:
            return jsonify({"status": "error", "message": "Görsel URL'i gereklidir"})

        # Görsel indir
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        # Dosya adı oluştur
        filename = f"resized_{os.path.basename(image_url)}"
        if '?' in filename:
            filename = filename.split('?')[0]

        if not filename.endswith(('.jpg', '.jpeg', '.png')):
            filename += '.jpg'

        output_path = os.path.join('static', 'images', filename)

        # Görsel boyutlandır
        if maintain_aspect:
            # En-boy oranını koru
            img.thumbnail((width, height), Image.LANCZOS)
        else:
            # Tam boyutlandırma
            img = img.resize((width, height), Image.LANCZOS)

        # Kaydet
        img.save(output_path)

        # Yeni boyutları al
        new_size = img.size

        # URL döndür
        return jsonify({
            "status": "success",
            "resized_url": f"/static/images/{filename}",
            "new_size": new_size
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)