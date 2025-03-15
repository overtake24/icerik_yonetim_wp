// Eğer alternatif hizalama seçiliyse bunu da ekle
        const alternatingAlignment = document.getElementById('alternating-alignment').checked;
        formData.append('alternating_alignment', alternatingAlignment ? '1' : '0');// Genel yardımcı fonksiyonlar
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Toast bildirimleri
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    const container = document.getElementById('toast-container');
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 3000);
}

// Anahtar kelime çevirisi ve resim yükleme
async function handleKeywordsInput(e) {
    const keywords = e.target.value;
    if (!keywords.trim()) {
        document.getElementById('translated-keywords').textContent = '';
        return;
    }

    try {
        console.log("Anahtar kelimeler çevriliyor:", keywords);
        document.getElementById('translated-keywords').textContent = '🔄 Çevriliyor...';

        const response = await fetch(`/translate_keywords?keywords=${encodeURIComponent(keywords)}`);
        const data = await response.json();

        let translatedKeywords = data.translated || keywords;

        if (data.error) {
            console.warn("Çeviri hatası:", data.error);
            document.getElementById('translated-keywords').textContent = `⚠️ Çeviri hatası, orijinal kelimeler kullanılıyor`;
            translatedKeywords = keywords; // Hata durumunda orijinal kelimeler
        } else if (data.translated && data.translated !== keywords) {
            document.getElementById('translated-keywords').textContent = `🔄 ${data.translated}`;

            // Etiketler boşsa, anahtar kelimeleri etiketlere kopyala
            const tagsInput = document.getElementById('tags');
            if (!tagsInput.value.trim()) {
                tagsInput.value = keywords;
            }
        } else {
            document.getElementById('translated-keywords').textContent = `ℹ️ Zaten İngilizce`;
        }

        console.log("Görseller alınıyor:", translatedKeywords);
        await fetchImages(keywords, translatedKeywords);

    } catch (error) {
        console.error('Çeviri hatası:', error);
        document.getElementById('translated-keywords').textContent = `⚠️ Çeviri servisine erişilemedi`;
        showToast('Çeviri sırasında bir hata oluştu, orijinal anahtar kelimeler kullanılıyor', 'warning');

        // Hata durumunda orijinal kelimelerle resim ara
        await fetchImages(keywords, keywords);
    }
}

// Resim yükleme - hem orijinal hem de çevrilmiş kelimeleri parametre olarak alır
async function fetchImages(originalKeywords, translatedKeywords) {
    const source = document.getElementById('source').value;
    const minWidth = document.getElementById('min-width').value;
    const minHeight = document.getElementById('min-height').value;

    // Yükleniyor göstergesi
    const imageGrid = document.getElementById('image-grid');
    imageGrid.innerHTML = '<div class="loading">Görseller yükleniyor...</div>';

    try {
        const response = await fetch(
            `/fetch_images?keywords=${encodeURIComponent(originalKeywords)}&translated_keywords=${encodeURIComponent(translatedKeywords)}&source=${source}&min_width=${minWidth}&min_height=${minHeight}`
        );
        const data = await response.json();

        imageGrid.innerHTML = ''; // Mevcut resimleri temizle

        if (!data.image_urls || data.image_urls.length === 0) {
            imageGrid.innerHTML = '<div class="error">Belirtilen kriterlere uygun görsel bulunamadı</div>';
            return;
        }

        data.image_urls.forEach((url, index) => {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'image-option';

            // Boyut bilgisini ekle, eğer varsa
            if (data.image_sizes && data.image_sizes[index]) {
                const [width, height] = data.image_sizes[index];
                imgContainer.dataset.width = width;
                imgContainer.dataset.height = height;

                // Boyut bilgisi etiketi
                const sizeLabel = document.createElement('div');
                sizeLabel.className = 'size-label';
                sizeLabel.textContent = `${width}×${height}`;
                imgContainer.appendChild(sizeLabel);
            }

            const img = document.createElement('img');
            img.src = url;
            img.alt = `${originalKeywords} görseli ${index + 1}`;
            img.loading = "lazy"; // Lazy loading ekle
            img.onerror = function() {
                // Görsel yüklenemezse hata mesajı
                imgContainer.innerHTML = '<div class="error">Görsel yüklenemedi</div>';
            };
            img.onclick = () => selectImage(url, imgContainer);

            // Görsel işlem menüsü
            const actionMenu = document.createElement('div');
            actionMenu.className = 'image-actions';

            const selectBtn = document.createElement('button');
            selectBtn.className = 'select-btn';
            selectBtn.innerHTML = '<span class="icon">✓</span>';
            selectBtn.title = 'Seç';
            selectBtn.onclick = (e) => {
                e.stopPropagation();
                selectImage(url, imgContainer);
            };

            const resizeBtn = document.createElement('button');
            resizeBtn.className = 'resize-btn';
            resizeBtn.innerHTML = '<span class="icon">↔</span>';
            resizeBtn.title = 'Boyutlandır';
            resizeBtn.onclick = (e) => {
                e.stopPropagation();
                showResizeModal(url, imgContainer);
            };

            actionMenu.appendChild(selectBtn);
            actionMenu.appendChild(resizeBtn);

            imgContainer.appendChild(img);
            imgContainer.appendChild(actionMenu);
            imageGrid.appendChild(imgContainer);
        });
    } catch (error) {
        console.error('Resim yükleme hatası:', error);
        imageGrid.innerHTML = '<div class="error">Görseller yüklenirken bir hata oluştu</div>';
        showToast('Görseller yüklenirken bir hata oluştu', 'error');
    }
}

// Boyutlandırma modalı
let currentResizeImage = null;

function showResizeModal(url, container) {
    // Modal içeriğini ayarla
    currentResizeImage = {
        url: url,
        container: container
    };

    // Mevcut boyutları göster
    if (container.dataset.width && container.dataset.height) {
        document.getElementById('resize-width').value = container.dataset.width;
        document.getElementById('resize-height').value = container.dataset.height;
    }

    // Modalı göster
    document.getElementById('resize-modal').style.display = 'block';
}

function closeResizeModal() {
    document.getElementById('resize-modal').style.display = 'none';
    currentResizeImage = null;
}

async function resizeSelectedImage() {
    if (!currentResizeImage) return;

    const width = document.getElementById('resize-width').value;
    const height = document.getElementById('resize-height').value;
    const maintainAspect = document.getElementById('maintain-aspect').checked;

    try {
        const response = await fetch('/resize_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_url: currentResizeImage.url,
                width: parseInt(width),
                height: parseInt(height),
                maintain_aspect: maintainAspect
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Başarılı olursa resmi güncelle
            const img = currentResizeImage.container.querySelector('img');
            img.src = data.resized_url + '?t=' + new Date().getTime(); // Cache'i önlemek için

            // Boyut bilgisini güncelle
            if (data.new_size) {
                const [newWidth, newHeight] = data.new_size;
                currentResizeImage.container.dataset.width = newWidth;
                currentResizeImage.container.dataset.height = newHeight;

                const sizeLabel = currentResizeImage.container.querySelector('.size-label');
                if (sizeLabel) {
                    sizeLabel.textContent = `${newWidth}×${newHeight}`;
                }
            }

            showToast('Görsel başarıyla boyutlandırıldı', 'success');
        } else {
            showToast('Boyutlandırma sırasında bir hata oluştu: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Boyutlandırma hatası:', error);
        showToast('Boyutlandırma sırasında bir hata oluştu', 'error');
    }

    closeResizeModal();
}

// Global değişkenler
let selectedImages = [];

// Resim seçimi
function selectImage(url, container) {
    const existingIndex = selectedImages.findIndex(img => img.url === url);

    if (existingIndex >= 0) {
        // Eğer resim zaten seçiliyse, seçimi kaldır
        selectedImages.splice(existingIndex, 1);
        container.classList.remove('selected');
    } else if (selectedImages.length < 4) {
        // Eğer 4'ten az resim seçiliyse, yeni resim ekle
        const imageData = {
            url: url,
            alignment: 'none',
            width: container.dataset.width || 0,
            height: container.dataset.height || 0
        };
        selectedImages.push(imageData);
        container.classList.add('selected');
    } else {
        showToast('En fazla 4 görsel seçebilirsiniz!', 'error');
        return;
    }

    updateSelectedImagesDisplay();
    updateSelectedCount();
}

function updateSelectedCount() {
    document.getElementById('selected-count').textContent = selectedImages.length;
}

function removeSelectedImage(url) {
    // Seçili görsellerden kaldır
    const index = selectedImages.findIndex(img => img.url === url);
    if (index >= 0) {
        selectedImages.splice(index, 1);
    }

    // İlgili konteynırın selected sınıfını kaldır
    const containers = document.querySelectorAll('.image-option');
    containers.forEach(container => {
        const img = container.querySelector('img');
        if (img && img.src === url) {
            container.classList.remove('selected');
        }
    });

    updateSelectedImagesDisplay();
    updateSelectedCount();
}

function updateSelectedImagesDisplay() {
    const container = document.getElementById('selected-images-list');
    const previewContainer = document.getElementById('preview-images');

    container.innerHTML = '';
    previewContainer.innerHTML = '';

    selectedImages.forEach((imgData, index) => {
        // Seçili görseller listesi için
        const div = document.createElement('div');
        div.className = 'selected-image-item';

        const img = document.createElement('img');
        img.src = imgData.url;
        img.alt = `Seçili görsel ${index + 1}`;

        // Hizalama seçici
        const alignmentSelect = document.createElement('select');
        alignmentSelect.className = 'image-alignment-select';
        alignmentSelect.innerHTML = `
            <option value="none" ${imgData.alignment === 'none' ? 'selected' : ''}>Hizalama Yok</option>
            <option value="left" ${imgData.alignment === 'left' ? 'selected' : ''}>Sola Hizala</option>
            <option value="center" ${imgData.alignment === 'center' ? 'selected' : ''}>Ortala</option>
            <option value="right" ${imgData.alignment === 'right' ? 'selected' : ''}>Sağa Hizala</option>
        `;
        alignmentSelect.onchange = (e) => {
            imgData.alignment = e.target.value;
            updatePreview();
        };

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-image';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removeSelectedImage(imgData.url);
        };

        div.appendChild(img);
        div.appendChild(alignmentSelect);
        div.appendChild(removeBtn);
        container.appendChild(div);

        // Önizleme için
        const previewImg = document.createElement('img');
        previewImg.src = imgData.url;
        previewImg.className = index === 0 ? 'featured-image' : 'content-image';

        // Görsel için Gutenberg hizalama sınıflarını ekle
        if (imgData.alignment !== 'none') {
            previewImg.classList.add(`align${imgData.alignment}`);
        }

        previewContainer.appendChild(previewImg);
    });
}

// Şablon işlemleri
function showNewTemplateModal() {
    document.getElementById('template-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('template-modal').style.display = 'none';
}

async function saveTemplate() {
    const name = document.getElementById('template-name').value;
    const content = document.getElementById('template-content').value;

    if (!name || !content) {
        alert('Lütfen şablon adı ve içeriği giriniz.');
        return;
    }

    try {
        const response = await fetch('/save_template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, content })
        });

        if (response.ok) {
            closeModal();
            location.reload(); // Şablon listesini yenile
        } else {
            alert('Şablon kaydedilirken bir hata oluştu.');
        }
    } catch (error) {
        console.error('Şablon kaydetme hatası:', error);
        alert('Şablon kaydedilirken bir hata oluştu.');
    }
}

// Form gönderimi
async function submitForm(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Seçili resim URL'lerini ekle
    if (selectedImages.length > 0) {
        // İlk resim öne çıkan görsel olarak ekle
        formData.append('image_url', selectedImages[0].url);

        // Tüm görsel URL'leri string olarak ekle
        const imageUrls = selectedImages.map(img => img.url);
        formData.append('image_urls', imageUrls.join(','));

        // İçerik görselleri (ilk görsel hariç)
        if (selectedImages.length > 1) {
            const contentImages = selectedImages.slice(1).map(img => ({
                url: img.url,
                alignment: img.alignment || 'none'
            }));

            // JSON string olarak ekle
            formData.append('content_images', JSON.stringify(contentImages));

            // Ayrıca düz URL'leri de ekle (yedek olarak)
            const contentImageUrls = selectedImages.slice(1).map(img => img.url);
            formData.append('content_image_urls', contentImageUrls.join(','));
        }
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            showToast('İçerik başarıyla gönderildi!', 'success');
            setTimeout(() => {
                location.reload(); // Sayfayı yenile
            }, 1500);
        } else {
            showToast('Bir hata oluştu: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Form gönderme hatası:', error);
        showToast('İçerik gönderilirken bir hata oluştu.', 'error');
    }

    return false;
}

// Önizleme güncelleme
function updatePreview() {
    const title = document.getElementById('title').value;
    const content = document.getElementById('content').value;
    const tags = document.getElementById('tags').value;

    document.getElementById('preview-title').textContent = title;

    // İçeriği paragraflar halinde formatlayarak göster
    const contentDiv = document.getElementById('preview-content');
    contentDiv.innerHTML = '';

    if (content) {
        const paragraphs = content.split('\n\n');
        paragraphs.forEach(p => {
            if (p.trim()) {
                const para = document.createElement('p');
                para.textContent = p.trim();
                contentDiv.appendChild(para);
            }
        });
    }

    // Etiketleri göster
    const tagsContainer = document.getElementById('preview-tags');
    tagsContainer.innerHTML = '';

    if (tags) {
        const tagsArray = tags.split(',');
        const tagsHeading = document.createElement('h4');
        tagsHeading.textContent = 'Etiketler:';
        tagsContainer.appendChild(tagsHeading);

        const tagsList = document.createElement('div');
        tagsList.className = 'tags-list';

        tagsArray.forEach(tag => {
            const tagSpan = document.createElement('span');
            tagSpan.className = 'tag';
            tagSpan.textContent = tag.trim();
            tagsList.appendChild(tagSpan);
        });

        tagsContainer.appendChild(tagsList);
    }

    // Seçili görselleri güncelle
    updateSelectedImagesDisplay();
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Anahtar kelime değişikliklerini dinle
    const keywordsInput = document.getElementById('keywords');
    keywordsInput.addEventListener('input', debounce(handleKeywordsInput, 500));

    // Resim kaynağı değişikliklerini dinle
    document.getElementById('source').addEventListener('change', () => {
        const keywords = document.getElementById('keywords').value;
        if (keywords) fetchImages(keywords);
    });

    // Minimum görsel boyutu değişikliklerini dinle
    document.getElementById('min-width').addEventListener('change', debounce(() => {
        const keywords = document.getElementById('keywords').value;
        if (keywords) fetchImages(keywords);
    }, 500));

    document.getElementById('min-height').addEventListener('change', debounce(() => {
        const keywords = document.getElementById('keywords').value;
        if (keywords) fetchImages(keywords);
    }, 500));

    // Görsel hizalama değişikliklerini ve alternatif hizalamayı dinle
    document.getElementById('featured-image-alignment').addEventListener('change', updatePreview);
    document.getElementById('content-image-alignment').addEventListener('change', updatePreview);
    document.getElementById('alternating-alignment').addEventListener('change', function() {
        // Alternatif hizalama seçildiğinde içerik görselleri seçiciyi devre dışı bırak
        const contentAlignSelect = document.getElementById('content-image-alignment');
        contentAlignSelect.disabled = this.checked;

        // Önizlemeyi güncelle
        updatePreview();
    });

    // Önizleme güncellemelerini dinle
    ['title', 'content', 'tags'].forEach(id => {
        document.getElementById(id).addEventListener('input', debounce(updatePreview, 300));
    });
});