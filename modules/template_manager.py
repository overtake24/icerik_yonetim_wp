import json
import os
from datetime import datetime
import html
from typing import Dict, List, Optional


class TemplateManager:
    def __init__(self):
        self.templates_file = "templates/saved_templates.json"
        self._ensure_template_file_exists()

    def _ensure_template_file_exists(self):
        if not os.path.exists(self.templates_file):
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "templates": {
                        "default": self._get_default_template()
                    }
                }, f, ensure_ascii=False, indent=2)

    def get_templates(self) -> Dict:
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # EOL formatını temizle eğer varsa
                if content.startswith("<< 'EOL'"):
                    content = content[len("<< 'EOL'"):].strip()
                if content.endswith("EOL"):
                    content = content[:-3].strip()

                return json.loads(content)["templates"]
        except Exception as e:
            print(f"Şablon okuma hatası: {e}")
            return {"default": self._get_default_template()}

    def _get_default_template(self) -> Dict:
        return {
            "name": "Varsayılan Blog Şablonu",
            "content": """<!-- wp:image {"align":"{image_alignment}","className":"featured-image"} -->
{featured_image}
<!-- /wp:image -->

<h1>{title}</h1>

{content}

<div class="content-images">
{content_images}
</div>

<hr/>
<p><strong>Etiketler:</strong> {tags}</p>""",
            "created_at": datetime.now().isoformat()
        }

    def save_template(self, name: str, content: str) -> None:
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

    def apply_template(self, template_name: str, **kwargs) -> str:
        try:
            templates = self.get_templates()
            if template_name not in templates:
                template_name = "default"

            template_content = templates[template_name]["content"]

            # Resim hizalaması
            image_alignment = kwargs.get('image_alignment', 'none')

            # Görselleri HTML formatına dönüştür
            kwargs['featured_image'] = self._format_featured_image(
                kwargs.get('featured_image', ''),
                kwargs.get('title', ''),
                image_alignment
            )

            if 'content_images' in kwargs and kwargs['content_images']:
                formatted_images = []

                # Gelen veriyi kontrol et ve düzenle
                content_images = kwargs['content_images']

                # String olarak geldiyse JSON parse et
                if isinstance(content_images, str):
                    try:
                        content_images = json.loads(content_images)
                    except:
                        # Parse edilemezse, virgülle ayrılmış URL listesi olarak kabul et
                        if ',' in content_images:
                            content_images = content_images.split(',')
                        else:
                            content_images = [content_images]

                # Liste değilse (tek nesne ise) listeye çevir
                if not isinstance(content_images, list):
                    content_images = [content_images]

                # Eğer alternatif hizalama isteniyorsa
                use_alternating = kwargs.get('alternating_alignment', False)

                for i, img_data in enumerate(content_images, 1):
                    try:
                        if isinstance(img_data, str):
                            # Eğer sadece URL ise
                            img_url = img_data

                            # Alternatif hizalama kullan
                            if use_alternating:
                                img_align = 'left' if i % 2 == 1 else 'right'
                            else:
                                img_align = kwargs.get('content_image_alignment', 'none')
                        else:
                            # Eğer dict ise (URL ve hizalama içeren)
                            img_url = img_data.get('url', '')
                            if not img_url and 'url' in img_data:
                                img_url = img_data['url']

                            # Alternatif hizalama kullan
                            if use_alternating:
                                img_align = 'left' if i % 2 == 1 else 'right'
                            else:
                                img_align = img_data.get('alignment', kwargs.get('content_image_alignment', 'none'))

                        # Boş URL kontrolü
                        if img_url:
                            formatted_images.append(
                                self._format_content_image(img_url, f"İçerik görseli {i}", img_align)
                            )
                    except Exception as e:
                        print(f"Görsel formatlarken hata: {e}, data: {img_data}")
                        # Hatayı yut ve devam et

                kwargs['content_images'] = '\n'.join(formatted_images)
            else:
                kwargs['content_images'] = ''

            # Diğer değişkenleri temizle ve formatla
            if 'title' in kwargs:
                kwargs['title'] = html.escape(kwargs['title'])
            if 'content' in kwargs:
                kwargs['content'] = self._format_content(kwargs['content'])
            if 'tags' in kwargs:
                kwargs['tags'] = self._format_tags(kwargs['tags'])

            # Image_alignment değerini template'e ekle
            kwargs['image_alignment'] = image_alignment

            return template_content.format(**kwargs)

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Şablon uygulama hatası: {str(e)}")

    def _format_featured_image(self, image_url: str, alt_text: str = '', alignment: str = 'none') -> str:
        if not image_url:
            return ''

        align_class = f"align{alignment}" if alignment != 'none' else ""

        # JSON içindeki çift tırnak kaçış karakterlerini düzgünce formatla
        return f"""<figure class="wp-block-image {align_class}">
    <img src="{image_url}" alt="{html.escape(alt_text)}" class="featured-image wp-post-image"/>
</figure>"""

    def _format_content_image(self, image_url: str, alt_text: str = '', alignment: str = 'none') -> str:
        align_class = f"align{alignment}" if alignment != 'none' else ""

        # JSON içindeki çift tırnak kaçış karakterlerini düzgünce formatla
        return f"""<!-- wp:image {{"align":"{alignment}"}} -->
<figure class="wp-block-image {align_class}">
    <img src="{image_url}" alt="{html.escape(alt_text)}" class="content-image"/>
</figure>
<!-- /wp:image -->"""

    def _format_content(self, content: str) -> str:
        paragraphs = content.split('\n\n')
        formatted = []
        for p in paragraphs:
            if p.strip():
                formatted.append(f'<!-- wp:paragraph -->\n<p>{html.escape(p.strip())}</p>\n<!-- /wp:paragraph -->')
        return '\n\n'.join(formatted)

    def _format_tags(self, tags: str) -> str:
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        return ', '.join(tag.strip() for tag in tags if tag.strip())