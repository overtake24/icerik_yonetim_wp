from jinja2 import Environment, FileSystemLoader


def generate_content(title, content, keywords, image_placeholder=False):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('post_template.jinja2')

    # Meta açıklamasını içerik içinden ilk 30 kelimeyi kullanarak oluştur
    words = content.split()
    meta_desc = " ".join(words[:30]) + "..." if len(words) > 30 else content

    # SEO için etiketleri düzenle
    tags = [keyword.strip() for keyword in keywords.split(',')]

    # Eğer görsel yerleşimi içeriğe eklenecekse bir yer tutucu ekle
    # Bu yer tutucu daha sonra wordpress_module.py tarafından gerçek görselle değiştirilecek
    if image_placeholder:
        # İçeriği paragraf paragraf böl
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 2:
            # İlk paragraftan sonra görsel için yer tutucu ekle
            # Bu kısım daha sonra gerçek görsel HTML'i ile değiştirilecek
            paragraphs.insert(1, '<!-- IMAGE_PLACEHOLDER -->')
            content = '\n\n'.join(paragraphs)

    return template.render(title=title, content=content, meta_desc=meta_desc, tags=tags)