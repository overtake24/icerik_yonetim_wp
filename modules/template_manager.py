import json
import os
from datetime import datetime
import html
import re
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
            "content": """<!-- wp:image {"align":"@image_alignment@","className":"featured-image"} -->
@featured_image@
<!-- /wp:image -->

<h1>@title@</h1>

@content@

<div class="content-images">
@content_images@
</div>

<hr/>
<p><strong>Etiketler:</strong> @tags@</p>""",
            "created_at": datetime.now().isoformat()
        }

    def save_template(self, name: str, content: str) -> None:
        try:
            templates = self.get_templates()
            # Convert '{' and '}' style placeholders to '@' style for new templates
            content = content.replace("{", "@").replace("}", "@")

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

            # Convert older templates using curly braces to our new format with '@' delimiters
            if "{" in template_content and "}" in template_content:
                # Replace simple variable placeholders but preserve WordPress block attributes
                template_content = self._convert_to_at_format(template_content)

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

                        # Bottom hizalama için özel işlem
                        if img_align == 'bottom':
                            # Yazının en altına ekle
                            formatted_images.append(
                                self._format_bottom_image(img_url, f"İçerik görseli {i}")
                            )
                        else:
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

            # Now replace all @variable@ style placeholders
            for key, value in kwargs.items():
                placeholder = f"@{key}@"
                template_content = template_content.replace(placeholder, str(value))

            # Remove any remaining @variable@ placeholders with empty strings
            template_content = re.sub(r'@\w+@', '', template_content)

            return template_content

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Şablon uygulama hatası: {e}")

            # Fallback to a very simple template if everything fails
            simple_content = f"<h1>{kwargs.get('title', '')}</h1>\n\n{kwargs.get('content', '')}"
            if kwargs.get('featured_image'):
                simple_content = f"<img src='{kwargs.get('featured_image', '')}' alt='{kwargs.get('title', '')}' />\n\n" + simple_content
            simple_content += f"\n\n<p><strong>Etiketler:</strong> {kwargs.get('tags', '')}</p>"

            return simple_content

    def _convert_to_at_format(self, template_content):
        """Convert curly brace format to @ format, preserving WordPress block attributes."""
        # First protect WordPress block attributes with a special marker
        protected_content = re.sub(
            r'(<!-- wp:.*?)(\{.*?\})(.*?-->)',
            lambda m: m.group(1) + '__PROTECTED__' + str(hash(m.group(2))) + '__PROTECTED__' + m.group(3),
            template_content
        )

        # Now convert regular variable placeholders
        protected_content = re.sub(
            r'\{([^{}]*)\}',
            r'@\1@',
            protected_content
        )

        # Restore protected WordPress block attributes
        for match in re.finditer(r'__PROTECTED__(-?\d+)__PROTECTED__', protected_content):
            hash_value = match.group(1)
            for original_match in re.finditer(r'(<!-- wp:.*?)(\{.*?\})(.*?-->)', template_content):
                if str(hash(original_match.group(2))) == hash_value:
                    protected_content = protected_content.replace(
                        f'__PROTECTED__{hash_value}__PROTECTED__',
                        original_match.group(2)
                    )
                    break

        return protected_content

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

        # Use double braces for JSON literals in WordPress blocks
        return f"""<!-- wp:image {{"align":"{alignment}"}} -->
<figure class="wp-block-image {align_class}">
    <img src="{image_url}" alt="{html.escape(alt_text)}" class="content-image"/>
</figure>
<!-- /wp:image -->"""

    def _format_bottom_image(self, image_url: str, alt_text: str = '') -> str:
        # Yazının altına eklenen görseller için özel format
        return f"""<!-- wp:image {{"align":"center"}} -->
<figure class="wp-block-image aligncenter">
    <img src="{image_url}" alt="{html.escape(alt_text)}" class="content-image bottom-image"/>
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