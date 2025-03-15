import json
import os
import time
import requests


class TranslationManager:
    def __init__(self):
        self.cache_file = "translation_cache.json"
        self._load_cache()
        self.translation_errors = 0
        self.max_errors = 3  # Arka arkaya bu kadar hata sonra çeviriden vazgeç

    def _load_cache(self):
        """Çeviri önbelleğini yükle."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = {}
        except Exception as e:
            print(f"Önbellek yükleme hatası: {e}")
            self._cache = {}

    def _save_cache(self):
        """Çeviri önbelleğini kaydet."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Önbellek kaydetme hatası: {e}")

    def reset_error_count(self):
        """Hata sayacını sıfırla."""
        self.translation_errors = 0

    def translate_to_english(self, text):
        """Metni İngilizce'ye çevir, daha güvenilir bir yaklaşımla."""
        # Boş metin kontrolü
        if not text or not text.strip():
            return text

        # Cache kontrolü
        if text in self._cache:
            print(f"Çeviri önbellekten bulundu: {text} -> {self._cache[text]}")
            return self._cache[text]

        # Arka arkaya çok fazla hata olduysa çeviriden vazgeç
        if self.translation_errors >= self.max_errors:
            print(f"Çok fazla çeviri hatası - çeviri devre dışı, orijinal metni kullanıyorum: {text}")
            return text

        try:
            print(f"Çevriliyor: {text}")
            # Önce bilinen basit Türkçe->İngilizce çevirimleri kontrol et
            tr_to_en = {
                "gezilecek yerler": "places to visit",
                "tatil": "vacation",
                "gezi": "travel",
                "tur": "tour",
                "rehber": "guide",
                "blog": "blog",
                "tarih": "history",
                "deniz": "sea",
                "plaj": "beach",
                "kültür": "culture",
                "yemek": "food",
                "otel": "hotel",
                "uçak": "airplane",
                "ulaşım": "transportation",
                "fotoğraf": "photography",
                "manzara": "landscape",
                "müze": "museum",
                "anıt": "monument",
                "mimari": "architecture",
                "doğa": "nature",
                "macera": "adventure",
                "seyahat": "travel",
                "keşif": "exploration"
            }

            # Basit kelime çevirisi
            lower_text = text.lower()
            for tr_word, en_word in tr_to_en.items():
                if tr_word in lower_text:
                    text = text.replace(tr_word, en_word)

            # Hala Türkçe kelimeler içeriyorsa, alternatif bir çeviri API'si dene
            try:
                # OPTION 1: LibreTranslate API (yerel kurulum veya ücretsiz API)
                # Kurulum: https://github.com/LibreTranslate/LibreTranslate
                # response = requests.post("https://libretranslate.com/translate",
                #     data={
                #         "q": text,
                #         "source": "auto",
                #         "target": "en"
                #     }
                # )
                # translated_text = response.json()["translatedText"]

                # OPTION 2: Çeviri için MyMemory API (ücretsiz)
                response = requests.get(
                    f"https://api.mymemory.translated.net/get?q={text}&langpair=tr|en"
                )
                result = response.json()
                if "responseStatus" in result and result["responseStatus"] == 200:
                    translated_text = result["responseData"]["translatedText"]

                    # Sonucu önbelleğe kaydet
                    self._cache[text] = translated_text
                    self._save_cache()

                    # Hata sayacını sıfırla
                    self.translation_errors = 0

                    return translated_text
                else:
                    # API hatası, orijinal metni döndür
                    print(f"API çeviri hatası: {result.get('responseStatus')}")
                    self.translation_errors += 1
                    return text

            except Exception as api_error:
                print(f"Çeviri API hatası: {api_error}")
                self.translation_errors += 1
                return text

        except Exception as e:
            print(f"Çeviri hatası: {e}")
            self.translation_errors += 1
            return text  # Hata durumunda orijinal metni döndür