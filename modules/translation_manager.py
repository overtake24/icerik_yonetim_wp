from googletrans import Translator
import time
import json
import os


class TranslationManager:
    def __init__(self):
        self.translator = Translator()
        self.cache_file = "translation_cache.json"
        self._load_cache()

    def _load_cache(self):
        """Çeviri önbelleğini yükle."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = {}
        except Exception:
            self._cache = {}

    def _save_cache(self):
        """Çeviri önbelleğini kaydet."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Önbellek kaydetme hatası: {e}")

    def translate_to_english(self, text):
        """Metni İngilizce'ye çevir."""
        # Boş metin kontrolü
        if not text or not text.strip():
            return text

        # Cache kontrolü
        if text in self._cache:
            return self._cache[text]

        try:
            # API limitlerine takılmamak için kısa bir bekleme
            time.sleep(0.5)

            # Metnin dilini otomatik algıla
            detection = self.translator.detect(text)

            # Eğer zaten İngilizceyse çevirme
            if detection.lang == 'en':
                return text

            # Çeviriyi yap
            translation = self.translator.translate(text, dest='en')

            # Cache'e kaydet
            self._cache[text] = translation.text
            self._save_cache()

            return translation.text
        except Exception as e:
            print(f"Çeviri hatası: {e}")
            return text  # Hata durumunda orijinal metni döndür