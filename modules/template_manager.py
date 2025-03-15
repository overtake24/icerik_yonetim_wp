import json
import os
from datetime import datetime
import html


class TemplateManager:
    def __init__(self):
        self.templates_file = "templates/saved_templates.json"
        self._ensure_template_file_exists()

    def _ensure_template_file_exists(self):
        """Şablon dosyasının varlığını kontrol et ve yoksa oluştur."""
        if not os.path.exists(self.templates_file):
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "templates": {
                        "default": {
                            "name": "Varsayılan Blog Şablonu",
                            "content": """
<!-- wp:image {"className":"featured-image"} -->
{featured_image}
<!-- /wp:image -->

<!-- wp:heading {"level":1} -->
<h1>{title}</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
{content}
<!-- /wp:paragraph -->

<!-- wp:gallery {"columns":2,"linkTo":"none","className":"content-images"} -->
<figure class="wp-block-gallery has-nested-images columns-2 is-cropped content-images">
{content_images}
</figure>
<!-- /wp:gallery -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":3} -->
<h3>📝 Yazı Bilgileri</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>Etiketler:</strong> {tags}</p>
<!-- /wp:paragraph -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:paragraph -->
<p><em>Not: Bu içerik otomatik olarak oluşturulmuştur.</em></p>
<!-- /wp:paragraph -->
""",
                            "created_at": datetime.now().isoformat()
                        }
                    }
                }, f, ensure_ascii=False, indent=2)

    def get_templates(self):
        """Tüm şablonları getir."""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)["templates"]
        except Exception as e:
            print(f"Şablon okuma hatası: {e}")
            return {"default": self._get_default_template()}

    def _get_default_template(self):
        """Varsayılan şablonu döndür."""
        return {
            "name": "Varsayılan Blog Şablonu",
            "content": """<!-- wp:image -->\n{featured_image}\n<!-- /wp:image -->\n\n<h1>{title}</h1>\n\n{content}\n\n{content_images}\n\nEtiketler: {tags}""",
            "created_at": datetime.now().isoformat()
        }

    def save_template(self, name, content):
        """Yeni şablon kaydet."""
        try:
            templates = self.get_templates()
            templates[name] = {
                "name": name,
                "content": content,
                "created_at": datetime.now().isoformat()
            }

            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump({"templates": templates}, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise Exception(f"Şablon kaydetme hatası: {str(e)}")

    def apply_template(self, template_name, **kwargs):
        """Şablonu uygula ve içeriği oluştur."""
        try:
            templates = self.get_templates()
            if template_name not in templates:
                template_name = "default"

            template_content = templates[template_name]["content"]

            # Görselleri HTML formatına dönüştür
            if 'featured_image' in kwargs and kwargs['featured_image']:
                kwargs['featured_image'] = self._format_featured_image(
                    kwargs['featured_image'],
                    kwargs.get('title', '')
                )
            else:
                kwargs['featured_image'] = ''

            if 'content_images' in kwargs and kwargs['content_images']:
                kwargs['content_images'] = self._format_content_images(
                    kwargs['content_images']
                )
            else:
                kwargs['content_images'] = ''

            # Diğer değişkenleri temizle
            if 'title' in kwargs:
                kwargs['title'] = html.escape(kwargs['title'])
            if 'content' in kwargs:
                kwargs['content'] = self._format_content(kwargs['content'])
            if 'tags' in kwargs:
                kwargs['tags'] = self._format_tags(kwargs['tags'])

            return template_content.format(**kwargs)

        except Exception as e:
            raise Exception(f"Şablon uygulama hatası: {str(e)}")

    def _format_featured_image(self, image_path, alt_text=''):
        """Öne çıkan görsel için HTML oluştur."""
        return f'<img src="{image_path}" alt="{html.escape(alt_text)}" class="featured-image"/>'

    def _format_content_images(self, image_paths):
        """İçerik görselleri için HTML oluştur."""
        image_html = {}
        for i, path in enumerate(image_paths, 1):
            image_html[
                f'content_image_{i}'] = f'<img src="{path}" alt="Berlin tarihi mekan {i}" class="content-image"/>'
        return image_html

    def _format_content(self, content):
        """İçeriği WordPress bloklarına uygun formata dönüştür."""
        paragraphs = content.split('\n\n')
        formatted = []
        for p in paragraphs:
            if p.strip():
                formatted.append(f'<!-- wp:paragraph -->\n<p>{html.escape(p.strip())}</p>\n<!-- /wp:paragraph -->')
        return '\n\n'.join(formatted)

    def _format_tags(self, tags):
        """Etiketleri WordPress için formatla."""
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]

        formatted_tags = []
        for tag in tags:
            if tag.strip():
                # Etiketleri düz metin olarak ekle
                formatted_tags.append(tag.strip())

        # Etiketleri virgülle ayırarak birleştir
        return ', '.join(formatted_tags)