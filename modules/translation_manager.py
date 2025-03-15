import json
import os
import time
import requests
import urllib.parse


class TranslationManager:
    def __init__(self):
        self.cache_file = "translation_cache.json"
        self._load_cache()
        self.translation_errors = 0
        self.max_errors = 3
        self.last_error_time = 0

        # Çeviri sistemi varsayılan olarak deaktif
        self.enabled = False

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
        self.last_error_time = 0

    def set_enabled(self, enabled):
        """Çeviri sistemini etkinleştir/devre dışı bırak."""
        self.enabled = enabled
        return self.enabled

    def translate_to_english(self, text):
        """Metni İngilizce'ye çevir, sistem aktifse."""
        # Çeviri devre dışı bırakıldıysa, metni olduğu gibi döndür
        if not self.enabled:
            print("Çeviri sistemi devre dışı, metin olduğu gibi kullanılıyor.")
            return text

        # Boş metin kontrolü
        if not text or not text.strip():
            return text

        # Cache kontrolü
        if text in self._cache:
            print(f"Çeviri önbellekten bulundu: {text} -> {self._cache[text]}")
            return self._cache[text]

        # Son hatadan bu yana belirli bir süre geçtiyse hata sayacını sıfırla (15 dakika)
        current_time = time.time()
        if self.last_error_time > 0 and current_time - self.last_error_time > 900:
            print("Hata sayacı sıfırlandı, çeviri tekrar denenecek.")
            self.translation_errors = 0

        # Arka arkaya çok fazla hata olduysa çeviriden vazgeç
        if self.translation_errors >= self.max_errors:
            print(f"Çok fazla çeviri hatası - çeviri devre dışı, orijinal metin kullanılıyor: {text}")
            return text

        try:
            print(f"Çevriliyor: {text}")
            # Bilinen Türkçe-İngilizce çevirimlerinden bazılarını kontrol et
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
                "müze": "museum",
                "şehir": "city",
                "doğa": "nature",
                "manzara": "landscape",
                "münih": "munich",
                "berlin": "berlin",
                "istanbul": "istanbul",
                "antalya": "antalya",
                "izmir": "izmir",
                "paris": "paris",
                "londra": "london",
                "roma": "rome",
                "atina": "athens",
                "barselona": "barcelona",
                "venedik": "venice",
                "almanya": "germany",
                "fransa": "france",
                "italya": "italy",
                "yunanistan": "greece",
                "ispanya": "spain"
                # İhtiyaca göre daha fazla kelime eklenebilir
            }

            # Basit kelime çevirisi
            original_text = text  # Orijinal metni saklayalım
            lower_text = text.lower()

            for tr_word, en_word in tr_to_en.items():
                if tr_word in lower_text:
                    text = text.replace(tr_word, en_word)

            # Eğer basit çeviri sonucunda metin değiştiyse, önbelleğe kaydet ve döndür
            if text != original_text:
                self._cache[original_text] = text
                self._save_cache()
                return text

            # Çeviri API dene
            try:
                # URL encode yapalım
                encoded_text = urllib.parse.quote(text)
                api_url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=tr|en"

                print(f"API isteği gönderiliyor: {api_url}")
                response = requests.get(api_url, timeout=10)

                if response.status_code != 200:
                    print(f"API yanıt kodu hatalı: {response.status_code}")
                    self.translation_errors += 1
                    self.last_error_time = time.time()
                    return text

                result = response.json()

                if "responseStatus" in result and result["responseStatus"] == 200:
                    translated_text = result["responseData"]["translatedText"]

                    # Sonucu önbelleğe kaydet
                    self._cache[original_text] = translated_text
                    self._save_cache()

                    # Hata sayacını sıfırla
                    self.translation_errors = 0
                    self.last_error_time = 0

                    return translated_text
                else:
                    # API yanıt hatası, detaylı bilgi alalım
                    error_msg = result.get("responseDetails", "Bilinmeyen API hatası")
                    print(f"API yanıt hatası: {error_msg}")
                    self.translation_errors += 1
                    self.last_error_time = time.time()
                    return text

            except requests.exceptions.RequestException as req_error:
                print(f"HTTP istek hatası: {req_error}")
                self.translation_errors += 1
                self.last_error_time = time.time()
                return text

            except Exception as api_error:
                print(f"Çeviri API hatası: {api_error}")
                self.translation_errors += 1
                self.last_error_time = time.time()
                return text

        except Exception as e:
            print(f"Genel çeviri hatası: {e}")
            self.translation_errors += 1
            self.last_error_time = time.time()
            return text  # Hata durumunda orijinal metni döndür