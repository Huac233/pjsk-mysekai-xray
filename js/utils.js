// 工具函数

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(func, wait);
    };
}

// 错误处理
function showError(message) {
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const controls = document.querySelector('.controls');
    controls.insertBefore(errorDiv, controls.firstChild);
    
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

// 加载指示器
function showLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
}

function hideLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

// 旋转向量应用
function applyRotationToVector(x, y, rotationDeg) {
    const rotationRad = -rotationDeg * Math.PI / 180;
    
    const cosA = Math.cos(rotationRad);
    const sinA = Math.sin(rotationRad);
    
    const newX = x * cosA - y * sinA;
    const newY = x * sinA + y * cosA;
    
    return { x: newX, y: newY };
}

// 计算重叠区域
function getOverlapArea(rect1, rect2) {
    const xOverlap = Math.max(0, Math.min(rect1.right, rect2.right) - Math.max(rect1.left, rect2.left));
    const yOverlap = Math.max(0, Math.min(rect1.bottom, rect2.bottom) - Math.max(rect1.top, rect2.top));
    return xOverlap * yOverlap;
}

// 获取唱片URL
function getMusicRecordUrl(recordId) {
    const recordData = MUSIC_RECORD_MAPPING[recordId];
    if (!recordData) {
        return './icon/Texture2D/item_surplus_music_record.png';
    }
    const { external_id, server } = recordData;
    const numId = parseInt(external_id);
    const formattedId = numId < 100 ? String(numId).padStart(3, '0') : String(numId);
    return `https://storage.sekai.best/sekai-${server}-assets/music/jacket/jacket_s_${formattedId}/jacket_s_${formattedId}.png`;
}

function getProxiedMusicRecordUrl(recordId, proxyIndex = 0) {
    const recordData = MUSIC_RECORD_MAPPING[recordId];
    if (!recordData) {
        return './icon/Texture2D/item_surplus_music_record.png';
    }
    const { external_id, server } = recordData;
    const numId = parseInt(external_id);
    const formattedId = numId < 100 ? String(numId).padStart(3, '0') : String(numId);
    const originalUrl = `https://storage.sekai.best/sekai-${server}-assets/music/jacket/jacket_s_${formattedId}/jacket_s_${formattedId}.png`;
    if (proxyIndex < PROXY_CONFIG.proxies.length) {
        const proxyUrl = PROXY_CONFIG.proxies[proxyIndex];
        return proxyUrl + encodeURIComponent(originalUrl);
    } else {
        return './icon/Texture2D/item_surplus_music_record.png';
    }
}