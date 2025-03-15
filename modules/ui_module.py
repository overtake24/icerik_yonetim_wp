from modules.history_manager import HistoryManager
from modules.template_manager import TemplateManager
from modules.image_module import fetch_and_resize_image, fetch_multiple_images
from modules.translation_manager import TranslationManager
from modules.content_module import generate_content
from datetime import datetime
import json
import traceback


def handle_form_submission(data, wp_client):
    history_manager = HistoryManager()
    template_manager = TemplateManager()
    translation_manager = TranslationManager()

    try:
        # Alternatif hizalama seçeneğini kontrol et
        alternating_alignment = data.get('alternating_alignment') == '1'

        # Anahtar kelimeleri çevir
        translated_keywords = translation_manager.translate_to_english(data['keywords'])

        # Görselleri hazırla
        image_urls = []

        # İlk olarak öne çıkan görsel için image_url'i kontrol et
        if 'image_url' in data and data['image_url']:
            image_urls.append(data['image_url'])

        # image_urls parametresini kontrol et
        if 'image_urls' in data and data['image_urls']:
            if isinstance(data['image_urls'], str):
                # Virgülle ayrılmış liste ise
                urls = [url.strip() for url in data['image_urls'].split(',')]
                for url in urls:
                    if url and url not in image_urls:
                        image_urls.append(url)
            elif isinstance(data['image_urls'], list):
                # Liste ise
                for url in data['image_urls']:
                    if url and url not in image_urls:
                        image_urls.append(url)

        # Eğer hiç görsel yoksa yeni görseller getir
        if not image_urls:
            print("Görsel bulunamadı, API ile yeni görseller getiriliyor...")
            try:
                fetched_urls, _ = fetch_multiple_images(
                    translated_keywords,
                    count=4,
                    source=data.get('source', 'pexels'),
                    min_width=int(data.get('min_width', 800)),
                    min_height=int(data.get('min_height', 600))
                )
                image_urls = fetched_urls
            except Exception as img_error:
                print(f"Görsel getirme hatası: {img_error}")
                # Hata olsa bile devam et, ancak log tut

        if not image_urls:
            print("Uyarı: Hiç görsel getirilemedi, içerik görselsiz olarak kullanılacak.")
            # Görselsiz de devam edebilir

        # İçerik görsellerini hazırla
        content_images = []

        # İçerik görselleri parametrelerini kontrol et
        if 'content_images' in data and data['content_images']:
            content_images_data = data['content_images']

            # String ise JSON olarak parse et
            if isinstance(content_images_data, str):
                try:
                    content_images_data = json.loads(content_images_data)
                except Exception as e:
                    print(f"JSON parse hatası: {e}")
                    # Virgülle ayrılmış liste ise
                    if ',' in content_images_data:
                        content_images_data = [url.strip() for url in content_images_data.split(',')]
                    else:
                        content_images_data = [content_images_data]

            # Liste değilse liste yap
            if not isinstance(content_images_data, list):
                content_images_data = [content_images_data]

            # İçerik görselleri (öne çıkan görsel hariç)
            for item in content_images_data:
                if isinstance(item, dict) and 'url' in item:
                    content_images.append({
                        'url': item['url'],
                        'alignment': item.get('alignment', data.get('content_image_alignment', 'none'))
                    })
                elif isinstance(item, str) and item:
                    content_images.append({
                        'url': item,
                        'alignment': data.get('content_image_alignment', 'none')
                    })

        # Yedek olarak content_image_urls parametresini kontrol et
        elif 'content_image_urls' in data and data['content_image_urls']:
            content_image_urls = data['content_image_urls']

            if isinstance(content_image_urls, str) and ',' in content_image_urls:
                urls = [url.strip() for url in content_image_urls.split(',')]
                for url in urls:
                    if url:
                        content_images.append({
                            'url': url,
                            'alignment': data.get('content_image_alignment', 'none')
                        })
            elif isinstance(content_image_urls, str) and content_image_urls.strip():
                content_images.append({
                    'url': content_image_urls.strip(),
                    'alignment': data.get('content_image_alignment', 'none')
                })

        # Eğer image_urls'den fazla görsel varsa ve content_images boşsa
        elif len(image_urls) > 1 and not content_images:
            for url in image_urls[1:]:  # İlk görsel hariç
                content_images.append({
                    'url': url,
                    'alignment': data.get('content_image_alignment', 'none')
                })

        # Handle content_image_1, content_image_2, etc. for the template
        content_image_placeholders = {}
        for i, img in enumerate(content_images, 1):
            if i <= 3:  # Only use first 3 images for placeholders
                img_url = img['url'] if isinstance(img, dict) else img
                img_alignment = img['alignment'] if isinstance(img, dict) and 'alignment' in img else 'none'
                content_image_placeholders[f'content_image_{i}'] = template_manager._format_content_image(
                    img_url, f"Content image {i}", img_alignment
                )

        # Etiketleri hazırla
        tags = data.get('tags', '')
        if not tags and 'keywords' in data:
            tags = data['keywords']  # Etiket yoksa anahtar kelimeleri kullan

        try:
            # Create template parameters
            template_params = {
                'title': data['title'],
                'content': data['content'],
                'tags': tags,
                'featured_image': image_urls[0] if image_urls else None,
                'content_images': content_images,
                'image_alignment': data.get('image_alignment', 'none'),
                'content_image_alignment': data.get('content_image_alignment', 'none'),
                'alternating_alignment': alternating_alignment,
                'date': datetime.now().strftime('%d.%m.%Y')
            }

            # Add individual content images
            template_params.update(content_image_placeholders)

            # Şablonu uygula
            template_name = data.get('template', 'default')
            formatted_content = template_manager.apply_template(
                template_name,
                **template_params
            )
        except Exception as template_error:
            print(f"Şablon uygulama hatası: {template_error}")
            traceback.print_exc()
            # Hata durumunda basit içerik üret
            formatted_content = f"<h1>{data['title']}</h1>\n\n{data['content']}"
            if image_urls:
                formatted_content = f"<img src='{image_urls[0]}' alt='{data['title']}' />\n\n" + formatted_content
            formatted_content += f"\n\n<p>Etiketler: {tags}</p>"

        # WordPress'e gönder
        publish_date = None
        if 'publish_date' in data and data['publish_date']:
            try:
                publish_date = datetime.strptime(data['publish_date'], '%Y-%m-%dT%H:%M')
            except Exception as e:
                print(f"Tarih çevirme hatası: {e}")

        try:
            post_id = wp_client.upload_post(
                data['title'],
                formatted_content,
                image_urls[0] if image_urls else None,
                publish_date,
                tags=tags.split(',') if isinstance(tags, str) else tags
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
        except Exception as wp_error:
            print(f"WordPress gönderim hatası: {wp_error}")
            traceback.print_exc()
            return {"status": "error", "message": f"WordPress'e gönderilirken bir hata oluştu: {str(wp_error)}"}

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": f"İşlem sırasında bir hata oluştu: {str(e)}"}