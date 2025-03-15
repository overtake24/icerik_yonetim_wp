from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.methods import taxonomies
from wordpress_xmlrpc.methods import posts
import os


class WordpressClient:
    def __init__(self, url, username, password):
        self.client = Client(url + "/xmlrpc.php", username, password)

    def upload_image(self, image_path):
        """WordPress'e resmi yükler ve ek dosya kimliğini döndürür."""
        if not os.path.exists(image_path):
            return None

        with open(image_path, 'rb') as img:
            data = {
                'name': os.path.basename(image_path),
                'type': 'image/jpeg',  # PNG kullanıyorsan image/png yap
                'bits': img.read(),
            }

            try:
                response = self.client.call(UploadFile(data))
                return {
                    'id': response['id'],
                    'url': response['url']  # Resim URL'sini de döndür
                }
            except Exception as e:
                print(f"Resim yükleme hatası: {e}")
                return None

    def upload_post(self, title, content, image_path, publish_date, tags=None):
        """WordPress'e yazıyı ek dosya kimliği ile birlikte yükler."""
        post = WordPressPost()
        post.title = title
        post.post_status = "publish"  # Zamanlamak istersen "future" kullan

        if publish_date:
            post.date = publish_date

        # Önce resmi yükle
        image_data = None
        if image_path and os.path.exists(image_path):
            image_data = self.upload_image(image_path)
        elif isinstance(image_path, str) and image_path.startswith('http'):
            # Doğrudan URL olarak geçildi
            post.content = content
        else:
            post.content = content

        if image_data:
            # Öne çıkan görsel olarak ayarla
            post.thumbnail = image_data['id']

            # İçeriğin başına resmi HTML olarak ekle
            img_html = f'<img src="{image_data["url"]}" alt="{title}" class="wp-post-image"/>'
            post.content = img_html + content
        else:
            post.content = content

        # Etiketleri ekle
        if tags:
            if isinstance(tags, str):
                # Virgülle ayrılmış string ise listeye çevir
                tag_list = [tag.strip() for tag in tags.split(',')]
            else:
                tag_list = tags

            post.terms_names = {
                'post_tag': tag_list
            }

        try:
            post_id = self.client.call(NewPost(post))
            return post_id
        except Exception as e:
            print(f"İçerik yükleme hatası: {e}")
            return None

    def get_image_alignment_options(self):
        """
        WordPress Gutenberg'den kullanılabilir resim hizalama seçeneklerini döndürür
        """
        return {
            'none': 'Hizalama Yok',
            'left': 'Sola Hizala',
            'center': 'Ortala',
            'right': 'Sağa Hizala',
            'wide': 'Geniş',
            'full': 'Tam Genişlik'
        }