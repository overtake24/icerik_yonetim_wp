from modules.history_manager import HistoryManager
from modules.template_manager import TemplateManager
from modules.image_module import fetch_and_resize_image, fetch_multiple_images
from modules.translation_manager import TranslationManager
from modules.content_module import generate_content
from datetime import datetime


def handle_form_submission(data, wp_client):
    history_manager = HistoryManager()
    template_manager = TemplateManager()
    translation_manager = TranslationManager()

    try:
        # Anahtar kelimeleri çevir
        translated_keywords = translation_manager.translate_to_english(data['keywords'])

        # Birden fazla görsel getir
        image_urls = []
        if 'image_urls' in data:
            image_urls = data['image_urls'].split(',')
        else:
            # Eğer görsel URL'leri yoksa yeni görseller getir
            image_urls = fetch_multiple_images(translated_keywords, count=4, source=data.get('source', 'pexels'))

        if not image_urls:
            return {"status": "error", "message": "Görsel alınırken bir hata oluştu."}

        # Şablonu uygula
        template_name = data.get('template', 'default')
        formatted_content = template_manager.apply_template(
            template_name,
            title=data['title'],
            content=data['content'],
            tags=data['keywords'],
            featured_image=image_urls[0] if image_urls else None,
            content_images=image_urls[1:] if len(image_urls) > 1 else []
        )

        # WordPress'e gönder
        publish_date = datetime.strptime(data['publish_date'], '%Y-%m-%dT%H:%M') if 'publish_date' in data else None
        post_id = wp_client.upload_post(
            data['title'],
            formatted_content,
            image_urls[0] if image_urls else None,
            publish_date
        )

        if post_id:
            # Veritabanına kaydet
            history_manager.save_post({
                'title': data['title'],
                'content': formatted_content,
                'keywords': data['keywords'],
                'image_url': image_urls[0] if image_urls else None,
                'template': template_name
            }, post_id)

            return {"status": "success", "message": "İçerik başarıyla WordPress'e gönderildi!"}
        else:
            return {"status": "error", "message": "WordPress'e gönderilirken bir hata oluştu."}

    except Exception as e:
        return {"status": "error", "message": f"İşlem sırasında bir hata oluştu: {str(e)}"}