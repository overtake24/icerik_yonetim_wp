import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv("config.env")


def fetch_image_url(keywords, source="pexels"):
    """Pexels veya Unsplash'tan resim URL'sini alır."""
    if not keywords:
        return None

    if source == "pexels":
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return None

        headers = {"Authorization": api_key}
        try:
            response = requests.get(f"https://api.pexels.com/v1/search?query={keywords}&per_page=1", headers=headers)
            response_json = response.json()

            if "photos" not in response_json or not response_json["photos"]:
                return None

            return response_json["photos"][0]["src"]["medium"]
        except Exception as e:
            print(f"Pexels API hatası: {e}")
            return None

    elif source == "unsplash":
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not access_key:
            return None

        try:
            response = requests.get(f"https://api.unsplash.com/photos/random?query={keywords}&client_id={access_key}")
            response_json = response.json()

            if "urls" not in response_json:
                return None

            return response_json["urls"]["regular"]
        except Exception as e:
            print(f"Unsplash API hatası: {e}")
            return None

    return None


def fetch_multiple_images(keywords, count=3, source="pexels"):
    """Pexels veya Unsplash'tan birden fazla resim URL'si alır."""
    if not keywords:
        return []

    image_urls = []

    if source == "pexels":
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return []

        headers = {"Authorization": api_key}
        try:
            response = requests.get(f"https://api.pexels.com/v1/search?query={keywords}&per_page={count}",
                                    headers=headers)
            response_json = response.json()

            if "photos" not in response_json or not response_json["photos"]:
                return []

            for photo in response_json["photos"]:
                image_urls.append(photo["src"]["medium"])

            return image_urls
        except Exception as e:
            print(f"Pexels API hatası: {e}")
            return []

    elif source == "unsplash":
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not access_key:
            return []

        try:
            response = requests.get(
                f"https://api.unsplash.com/photos/random?query={keywords}&count={count}&client_id={access_key}")
            response_json = response.json()

            if not isinstance(response_json, list):
                return []

            for photo in response_json:
                if "urls" in photo:
                    image_urls.append(photo["urls"]["regular"])

            return image_urls
        except Exception as e:
            print(f"Unsplash API hatası: {e}")
            return []

    return []


def fetch_and_resize_image(keywords, source="pexels"):
    """Seçilen API kaynağından resmi alır, boyutlandırır ve kaydeder."""
    if not keywords:
        return None

    image_url = fetch_image_url(keywords, source)
    if not image_url:
        return None

    try:
        img_response = requests.get(image_url)
        img = Image.open(BytesIO(img_response.content))

        # Klasörün var olduğundan emin ol
        os.makedirs("static", exist_ok=True)

        resized_img_path = "static/resized_image.jpg"

        # PIL sürümüne göre doğru yöntemi kullan
        try:
            img = img.resize((800, 600), Image.Resampling.LANCZOS)  # Python 3.10+ için
        except AttributeError:
            img = img.resize((800, 600), Image.LANCZOS)  # Eski PIL sürümleri için

        img.save(resized_img_path)

        return resized_img_path
    except Exception as e:
        print(f"Görsel indirme/boyutlandırma hatası: {e}")
        return None