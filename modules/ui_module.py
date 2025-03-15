import os
from modules.image_module import fetch_and_resize_image
from modules.content_module import generate_content
from dotenv import load_dotenv

load_dotenv("config.env")


def handle_form_submission(data, wp_client):
    # Anahtar kelimeleri kullanarak görsel getir
    image_path = fetch_and_resize_image(data['keywords'], data.get('source', 'pexels'))

    if not image_path:
        return "Görsel alınırken bir hata oluştu. Lütfen anahtar kelimeleri kontrol edin."

    # İçeriği formatla
    formatted_content = generate_content(
        data['title'],
        data['content'],
        data['keywords'],
        image_placeholder=True
    )

    # WordPress'e gönder
    result = wp_client.upload_post(
        data['title'],
        formatted_content,
        image_path,
        data.get('publish_date')
    )

    if result:
        return "İçerik başarıyla WordPress'e gönderildi!"
    else:
        return "İçerik gönderilirken bir hata oluştu. Lütfen bağlantı bilgilerinizi kontrol edin."