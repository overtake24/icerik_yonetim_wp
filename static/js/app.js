// Genel yardımcı fonksiyonlar
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

// Anahtar kelime çevirisi ve resim yükleme
async function handleKeywordsInput(e) {
    const keywords = e.target.value;
    if (!keywords.trim()) return;

    try {
        const response = await fetch(`/translate_keywords?keywords=${encodeURIComponent(keywords)}`);
        const data = await response.json();

        if (data.translated && data.translated !== keywords) {
            document.getElementById('translated-keywords').textContent = `🔄 ${data.translated}`;
            await fetchImages(data.translated);
        }
    } catch (error) {
        console.error('Çeviri hatası:', error);
    }
}

// Resim yükleme
async function fetchImages(keywords) {
    const source = document.getElementById('source').value;
    try {
        const response = await fetch(`/fetch_images?keywords=${encodeURIComponent(keywords)}&source=${source}`);
        const data = await response.json();

        const imageGrid = document.getElementById('image-grid');
        imageGrid.innerHTML = ''; // Mevcut resimleri temizle

        data.image_urls.forEach(url => {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'image-option';

            const img = document.createElement('img');
            img.src = url;
            img.onclick = () => selectImage(url, imgContainer);

            imgContainer.appendChild(img);
            imageGrid.appendChild(imgContainer);
        });
    } catch (error) {
        console.error('Resim yükleme hatası:', error);
    }
}

// Global değişkenler
let selectedImages = new Set();

// Resim seçimi
function selectImage(url, container) {
    if (selectedImages.has(url)) {
        // Eğer resim zaten seçiliyse, seçimi kaldır
        selectedImages.delete(url);
        container.classList.remove('selected');
    } else if (selectedImages.size < 4) {
        // Eğer 4'ten az resim seçiliyse, yeni resim ekle
        selectedImages.add(url);
        container.classList.add('selected');
    } else {
        showToast('En fazla 4 görsel seçebilirsiniz!', 'error');
        return;
    }

    updateSelectedImagesDisplay();
    updateSelectedCount();
}

function updateSelectedImagesDisplay() {
    const container = document.getElementById('selected-images-list');
    const previewContainer = document.getElementById('preview-images');

    container.innerHTML = '';
    previewContainer.innerHTML = '';

    [...selectedImages].forEach((url, index) => {
        // Seçili görseller listesi için
        const div = document.createElement('div');
        div.className = 'selected-image-item';

        const img = document.createElement('img');
        img.src = url;
        img.alt = `Seçili görsel ${index + 1}`;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-image';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removeSelectedImage(url);
        };

        div.appendChild(img);
        div.appendChild(removeBtn);
        container.appendChild(div);

        // Önizleme için
        const previewImg = document.createElement('img');
        previewImg.src = url;
        previewImg.className = index === 0 ? 'featured-image' : 'content-image';
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

    // Seçili resim URL'sini ekle
    const selectedImage = document.querySelector('.image-option.selected img');
    if (selectedImage) {
        formData.append('image_url', selectedImage.src);
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            alert('İçerik başarıyla gönderildi!');
            location.reload(); // Sayfayı yenile
        } else {
            alert('Bir hata oluştu: ' + result.message);
        }
    } catch (error) {
        console.error('Form gönderme hatası:', error);
        alert('İçerik gönderilirken bir hata oluştu.');
    }

    return false;
}

// Önizleme güncelleme
function updatePreview() {
    const title = document.getElementById('title').value;
    const content = document.getElementById('content').value;

    document.getElementById('preview-title').textContent = title;
    document.getElementById('preview-content').textContent = content;
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

    // Önizleme güncellemelerini dinle
    ['title', 'content'].forEach(id => {
        document.getElementById(id).addEventListener('input', updatePreview);
    });
});