import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import urllib.parse  # URL encoding için eklendi

load_dotenv("config.env")


def fetch_image_url(keywords, source="pexels", min_width=800, min_height=600):
    """Pexels veya Unsplash'tan minimum boyut kriterini karşılayan resim URL'sini alır."""
    if not keywords:
        return None, None

    if source == "pexels":
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            print("Pexels API anahtarı bulunamadı.")
            return None, None

        headers = {"Authorization": api_key}
        try:
            # URL encode yapalım
            encoded_keywords = urllib.parse.quote(keywords)
            api_url = f"https://api.pexels.com/v1/search?query={encoded_keywords}&per_page=15"

            print(f"Pexels API isteği gönderiliyor: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"Pexels API yanıt kodu hatalı: {response.status_code}")
                return None, None

            response_json = response.json()

            if "photos" not in response_json or not response_json["photos"]:
                print(f"Pexels API sonuç bulunamadı.")
                return None, None

            # Boyut kriterine göre filtrele
            for photo in response_json["photos"]:
                width = photo["width"]
                height = photo["height"]
                if width >= min_width and height >= min_height:
                    return photo["src"]["medium"], (width, height)

            # Eğer hiçbir resim minimum boyut kriterini karşılamazsa, en büyük olanı döndür
            if response_json["photos"]:
                largest_photo = max(response_json["photos"], key=lambda p: p["width"] * p["height"])
                return largest_photo["src"]["medium"], (largest_photo["width"], largest_photo["height"])

            return None, None
        except Exception as e:
            print(f"Pexels API hatası: {e}")
            return None, None

    elif source == "unsplash":
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not access_key:
            print("Unsplash API anahtarı bulunamadı.")
            return None, None

        try:
            # URL encode yapalım
            encoded_keywords = urllib.parse.quote(keywords)
            api_url = f"https://api.unsplash.com/photos/random?query={encoded_keywords}&count=10&client_id={access_key}"

            print(f"Unsplash API isteği gönderiliyor: {api_url}")
            response = requests.get(api_url, timeout=15)

            if response.status_code != 200:
                print(f"Unsplash API yanıt kodu hatalı: {response.status_code}")
                return None, None

            response_json = response.json()

            if not isinstance(response_json, list) or not response_json:
                print(f"Unsplash API sonuç bulunamadı.")
                return None, None

            # Boyut kriterine göre filtrele
            for photo in response_json:
                if "width" in photo and "height" in photo:
                    width = photo["width"]
                    height = photo["height"]
                    if width >= min_width and height >= min_height:
                        return photo["urls"]["regular"], (width, height)

            # Eğer hiçbir resim minimum boyut kriterini karşılamazsa, en büyük olanı döndür
            if response_json:
                largest_photo = max(response_json, key=lambda p: p.get("width", 0) * p.get("height", 0))
                return largest_photo["urls"]["regular"], (largest_photo.get("width", 0), largest_photo.get("height", 0))

            return None, None
        except Exception as e:
            print(f"Unsplash API hatası: {e}")
            return None, None

    return None, None


def fetch_multiple_images(keywords, count=3, source="pexels", min_width=800, min_height=600):
    """Pexels veya Unsplash'tan minimum boyut kriterini karşılayan birden fazla resim URL'si alır."""
    if not keywords:
        return [], []

    image_urls = []
    image_sizes = []

    if source == "pexels":
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            print("Pexels API anahtarı bulunamadı.")
            return [], []

        headers = {"Authorization": api_key}
        try:
            # URL encode yapalım
            encoded_keywords = urllib.parse.quote(keywords)
            api_url = f"https://api.pexels.com/v1/search?query={encoded_keywords}&per_page={count * 3}"

            print(f"Pexels API isteği gönderiliyor (çoklu görseller): {api_url}")
            response = requests.get(api_url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"Pexels API yanıt kodu hatalı: {response.status_code}")
                return [], []

            response_json = response.json()

            if "photos" not in response_json or not response_json["photos"]:
                print(f"Pexels API sonuç bulunamadı (çoklu görseller).")
                return [], []

            # Boyut bilgisiyle birlikte resimleri depola
            filtered_photos = []
            for photo in response_json["photos"]:
                width = photo["width"]
                height = photo["height"]
                if width >= min_width and height >= min_height:
                    filtered_photos.append({
                        "url": photo["src"]["medium"],
                        "width": width,
                        "height": height
                    })

            # Yeterli sayıda resim bulunamadıysa, boyut kriterini karşılamayanları da ekle
            if len(filtered_photos) < count:
                for photo in response_json["photos"]:
                    if not any(fp["url"] == photo["src"]["medium"] for fp in filtered_photos):
                        filtered_photos.append({
                            "url": photo["src"]["medium"],
                            "width": photo["width"],
                            "height": photo["height"]
                        })
                    if len(filtered_photos) >= count:
                        break

            # İstenen sayıda resim URL'si döndür
            for photo in filtered_photos[:count]:
                image_urls.append(photo["url"])
                image_sizes.append((photo["width"], photo["height"]))

            return image_urls, image_sizes
        except Exception as e:
            print(f"Pexels API hatası (çoklu görseller): {e}")
            return [], []

    elif source == "unsplash":
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not access_key:
            print("Unsplash API anahtarı bulunamadı.")
            return [], []

        try:
            # URL encode yapalım
            encoded_keywords = urllib.parse.quote(keywords)
            api_url = f"https://api.unsplash.com/photos/random?query={encoded_keywords}&count={count * 2}&client_id={access_key}"

            print(f"Unsplash API isteği gönderiliyor (çoklu görseller): {api_url}")
            response = requests.get(api_url, timeout=15)

            if response.status_code != 200:
                print(f"Unsplash API yanıt kodu hatalı: {response.status_code}")
                return [], []

            response_json = response.json()

            if not isinstance(response_json, list):
                print(f"Unsplash API sonuç bulunamadı (çoklu görseller).")
                return [], []

            # Boyut bilgisiyle birlikte resimleri depola
            filtered_photos = []
            for photo in response_json:
                if "urls" in photo and "width" in photo and "height" in photo:
                    width = photo["width"]
                    height = photo["height"]
                    if width >= min_width and height >= min_height:
                        filtered_photos.append({
                            "url": photo["urls"]["regular"],
                            "width": width,
                            "height": height
                        })

            # Yeterli sayıda resim bulunamadıysa, boyut kriterini karşılamayanları da ekle
            if len(filtered_photos) < count:
                for photo in response_json:
                    if "urls" in photo and not any(fp["url"] == photo["urls"]["regular"] for fp in filtered_photos):
                        filtered_photos.append({
                            "url": photo["urls"]["regular"],
                            "width": photo.get("width", 0),
                            "height": photo.get("height", 0)
                        })
                    if len(filtered_photos) >= count:
                        break

            # İstenen sayıda resim URL'si döndür
            for photo in filtered_photos[:count]:
                image_urls.append(photo["url"])
                image_sizes.append((photo["width"], photo["height"]))

            return image_urls, image_sizes
        except Exception as e:
            print(f"Unsplash API hatası (çoklu görseller): {e}")
            return [], []

    return [], []


def fetch_and_resize_image(keywords, source="pexels", target_width=800, target_height=600):
    """Seçilen API kaynağından resmi alır, boyutlandırır ve kaydeder."""
    if not keywords:
        return None

    image_url, size = fetch_image_url(keywords, source)
    if not image_url:
        return None

    try:
        img_response = requests.get(image_url)
        img = Image.open(BytesIO(img_response.content))

        # Klasörün var olduğundan emin ol
        os.makedirs("static/images", exist_ok=True)

        resized_img_path = f"static/images/{keywords.replace(' ', '_')}_{source}.jpg"

        # PIL sürümüne göre doğru yöntemi kullan
        try:
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)  # Python 3.10+ için
        except AttributeError:
            img = img.resize((target_width, target_height), Image.LANCZOS)  # Eski PIL sürümleri için

        img.save(resized_img_path)

        return resized_img_path
    except Exception as e:
        print(f"Görsel indirme/boyutlandırma hatası: {e}")
        return None