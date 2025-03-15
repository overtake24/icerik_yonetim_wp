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
                return json.load(f)["templates"]
        except Exception as e:
            print(f"Şablon okuma hatası: {e}")
            return {"default": self._get_default_template()}

    def _get_default_template(self) -> Dict:
        return {
            "name": "Varsayılan Blog Şablonu",
            "content": """<!-- wp:image {{"className":"featured-image"}} -->
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

            # Görselleri HTML formatına dönüştür
            kwargs['featured_image'] = self._format_featured_image(
                kwargs.get('featured_image', ''),
                kwargs.get('title', '')
            )

            if 'content_images' in kwargs and kwargs['content_images']:
                formatted_images = []
                for i, img_url in enumerate(kwargs['content_images'], 1):
                    formatted_images.append(
                        self._format_content_image(img_url, f"İçerik görseli {i}")
                    )
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

            return template_content.format(**kwargs)

        except Exception as e:
            raise Exception(f"Şablon uygulama hatası: {str(e)}")

    def _format_featured_image(self, image_url: str, alt_text: str = '') -> str:
        if not image_url:
            return ''
        return f'<img src="{image_url}" alt="{html.escape(alt_text)}" class="featured-image wp-post-image"/>'

    def _format_content_image(self, image_url: str, alt_text: str = '') -> str:
        return f'<img src="{image_url}" alt="{html.escape(alt_text)}" class="content-image"/>'

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