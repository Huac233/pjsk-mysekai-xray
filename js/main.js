// 主应用程序逻辑

let allPoints = { scene1: [], scene2: [], scene3: [], scene4: [] };
let allItemLists = { scene1: [], scene2: [], scene3: [], scene4: [] };
let sceneRotations = { scene1: 0, scene2: 0, scene3: 0, scene4: 0 };
let resizeTimeout;
let globalXDirection = 'x+';
let globalYDirection = 'y-';
let globalReverseXY = false;

const images = {
    scene1: document.getElementById('image1'),
    scene2: document.getElementById('image2'),
    scene3: document.getElementById('image3'),
    scene4: document.getElementById('image4')
};

const canvases = {
    scene1: document.getElementById('gridCanvas1'),
    scene2: document.getElementById('gridCanvas2'),
    scene3: document.getElementById('gridCanvas3'),
    scene4: document.getElementById('gridCanvas4')
};

const containers = {
    scene1: document.getElementById('container1'),
    scene2: document.getElementById('container2'),
    scene3: document.getElementById('container3'),
    scene4: document.getElementById('container4')
};

const imageContainers = {
    scene1: document.getElementById('imageContainer1'),
    scene2: document.getElementById('imageContainer2'),
    scene3: document.getElementById('imageContainer3'),
    scene4: document.getElementById('imageContainer4')
};

const rotationIndicators = {
    scene1: document.getElementById('rotationIndicator1'),
    scene2: document.getElementById('rotationIndicator2'),
    scene3: document.getElementById('rotationIndicator3'),
    scene4: document.getElementById('rotationIndicator4')
};

const physicalWidthInput = document.getElementById('physicalWidth');
const offsetXInput = document.getElementById('offsetX');
const offsetYInput = document.getElementById('offsetY');
const jsonInput = document.getElementById('jsonInput');
const loadingIndicator = document.getElementById('loadingIndicator');

if (!window.deleteHistory) {
    window.deleteHistory = {
        scene1: [],
        scene2: [],
        scene3: [],
        scene4: []
    };
}

window.addEventListener('resize', debounce(function() {
    initCanvases();
    
    if (jsonInput.value && hasValidData()) {
        parseAndMarkPoints();
    }
}, 250));

window.addEventListener('resize', initCanvases);

function hasValidData() {
    try {
        const inputText = jsonInput.value;
        if (!inputText.trim()) {
            return false;
        }
        
        const parsedData = parseInputText(inputText);
        return Object.keys(parsedData).length > 0;
    } catch (error) {
        return false;
    }
}

function parseAndMarkPoints() {
    try {
        const inputText = jsonInput.value;
        if (!inputText.trim()) {
            showError('请输入JSON数据');
            return;
        }

        const parsedData = parseInputText(inputText);
        const selectedScenes = getSelectedScenes();

        if (selectedScenes.length === 0) {
            showError('请至少选择一个场景');
            return;
        }

        clearAll();
        initCanvases();

        const imageLoadPromises = Object.keys(images).map(key => {
            return new Promise((resolve) => {
                if (images[key].complete) {
                    resolve();
                } else {
                    images[key].onload = resolve;
                    images[key].onerror = resolve;
                }
            });
        });

        Promise.all(imageLoadPromises).then(() => {
            Object.keys(parsedData).forEach(siteName => {
                const sceneKey = SITE_TO_SCENE[siteName];
                if (sceneKey && selectedScenes.includes(sceneKey)) {
                    applySceneToMap(sceneKey);
                    const points = parsedData[siteName];
                    if (!Array.isArray(points)) {
                        throw new Error(`数据格式错误 for ${siteName}`);
                    }
                    const scene = SCENES[sceneKey];
                    const currentXDirection = scene.xDirection;
                    const currentYDirection = scene.yDirection;
                    const currentReverseXY = scene.reverseXY;
                    const canvas = canvases[sceneKey];
                    const ctx = canvas.getContext('2d');
                    allPoints[sceneKey] = [];
                    allItemLists[sceneKey] = [];
                    
                    addUndoButton(sceneKey);
                    
                    if (!currentReverseXY) {
                        points.forEach(point => markPointForScene(sceneKey, point, currentXDirection, currentYDirection));
                    } else {
                        points.forEach(point => markPointForScene(sceneKey, 
                            {location: [point.location[1], point.location[0]], 
                             fixtureId: point.fixtureId, 
                             reward: point.reward}, 
                            currentXDirection, currentYDirection));
                    }
                    
                    optimizeItemListPositionsForScene(sceneKey);
                    drawConnectionLinesForScene(sceneKey);
                }
            });
        });
    } catch (error) {
        console.error('解析错误:', error);
        showError("解析错误: " + error.message);
    }
}

function addUndoButton(sceneKey) {
    const container = containers[sceneKey];
    if (!container) return;
    
    let undoContainer = document.getElementById(`undoContainer-${sceneKey}`);
    
    if (!undoContainer) {
        undoContainer = document.createElement('div');
        undoContainer.id = `undoContainer-${sceneKey}`;
        undoContainer.className = 'undo-container';
        
        const undoBtn = document.createElement('button');
        undoBtn.id = `undoBtn-${sceneKey}`;
        undoBtn.className = 'undo-btn';
        undoBtn.innerHTML = '↶';
        undoBtn.title = '撤回删除';
        undoBtn.disabled = true;
        
        undoBtn.addEventListener('click', function() {
            undoDelete(sceneKey);
        });
        
        const tooltip = document.createElement('div');
        tooltip.id = `undoTooltip-${sceneKey}`;
        tooltip.className = 'undo-tooltip';
        tooltip.textContent = '撤回删除';
        
        undoContainer.appendChild(undoBtn);
        undoContainer.appendChild(tooltip);
        container.appendChild(undoContainer);
    }
}

function parseInputText(text) {
    const lines = text.split('\n');
    const data = {};
    let currentSite = null;
    let jsonBuffer = '';
    
    lines.forEach(line => {
        const siteMatch = line.match(/Site: (.*)/);
        if (siteMatch) {
            if (currentSite && jsonBuffer) {
                try {
                    data[currentSite] = JSON.parse(jsonBuffer);
                } catch (e) {
                    console.error('JSON解析错误:', e);
                    throw new Error(`站点 ${currentSite} 的JSON数据格式错误`);
                }
            }
            currentSite = siteMatch[1].trim();
            jsonBuffer = '';
        } else if (currentSite && line.trim().startsWith('[')) {
            jsonBuffer = line.trim();
        }
    });
    
    if (currentSite && jsonBuffer) {
        try {
            data[currentSite] = JSON.parse(jsonBuffer);
        } catch (e) {
            console.error('JSON解析错误:', e);
            throw new Error(`站点 ${currentSite} 的JSON数据格式错误`);
        }
    }
    
    if (Object.keys(data).length === 0) {
        throw new Error('未找到有效的站点数据');
    }
    
    return data;
}

function getSelectedScenes() {
    const checkboxes = document.querySelectorAll('.scene-checkboxes input[type="checkbox"]');
    return Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
}

function applySceneToMap(sceneKey) {
    const selectedScene = SCENES[sceneKey];
    if (selectedScene && images[sceneKey]) {
        images[sceneKey].src = selectedScene.imagePath;
    }
}

function setDirection(newXDirection, newYDirection) {
    globalXDirection = newXDirection;
    globalYDirection = newYDirection;
    parseAndMarkPoints();
}

function clearItemListsForScene(sceneKey) {
    const container = containers[sceneKey];
    container.querySelectorAll('.item-list').forEach(item => item.remove());
    container.querySelectorAll('.connection-line').forEach(line => line.remove());
    container.querySelectorAll('.undo-container').forEach(container => container.remove());
    if (magneticGuides[sceneKey]) {
        magneticGuides[sceneKey].remove();
        magneticGuides[sceneKey] = null;
    }
    allPoints[sceneKey] = [];
    allItemLists[sceneKey] = [];
    
    if (window.deleteHistory && window.deleteHistory[sceneKey]) {
        window.deleteHistory[sceneKey] = [];
    }
}

function clearAll() {
    Object.keys(canvases).forEach(key => {
        const ctx = canvases[key].getContext('2d');
        ctx.clearRect(0, 0, canvases[key].width, canvases[key].height);
        clearItemListsForScene(key);
    });
}

function rotateScene(sceneKey, angle) {
    sceneRotations[sceneKey] = (sceneRotations[sceneKey] + angle) % 360;
    if (sceneRotations[sceneKey] < 0) {
        sceneRotations[sceneKey] += 360;
    }
    
    const imageContainer = imageContainers[sceneKey];
    imageContainer.style.transform = `rotate(${sceneRotations[sceneKey]}deg)`;
    
    rotationIndicators[sceneKey].textContent = `当前角度: ${sceneRotations[sceneKey]}°`;
    
    const itemLists = allItemLists[sceneKey] || [];
    itemLists.forEach(itemList => {
        itemList.style.transform = `rotate(${-sceneRotations[sceneKey]}deg)`;
    });
    
    drawConnectionLinesForScene(sceneKey);
}

function resetRotation(sceneKey) {
    sceneRotations[sceneKey] = 0;
    const imageContainer = imageContainers[sceneKey];
    imageContainer.style.transform = 'rotate(0deg)';
    
    rotationIndicators[sceneKey].textContent = '当前角度: 0°';
    
    const itemLists = allItemLists[sceneKey] || [];
    itemLists.forEach(itemList => {
        itemList.style.transform = 'rotate(0deg)';
    });
    
    drawConnectionLinesForScene(sceneKey);
}

function getBrowserZoomLevel() {
    const zoomLevel = Math.round(window.devicePixelRatio * 100);
    return zoomLevel;
}

async function captureScreenshots() {
    if (window.location.protocol === 'file:') {
        alert('截图功能在file://协议下不可用，请使用以下方法之一：\n\n1. 使用Python HTTP服务器：\n   python -m http.server\n\n使用http://localhost:8000访问此页面。2. 使用Github page部署的网页');
        return;
    }

    const zoomLevel = getBrowserZoomLevel();
    if (zoomLevel !== 100) {
        const shouldContinue = confirm(`检测到浏览器缩放为${zoomLevel}%，截图可能会出现物品布局异常。\n\n建议将浏览器缩放设置为100%后再进行截图，以获得最佳效果。\n\n是否继续截图？`);
        if (!shouldContinue) {
            return;
        }
    }

    const selectedScenes = getSelectedScenes();
    
    if (selectedScenes.length === 0) {
        alert('请至少选择一个场景进行截图');
        return;
    }

    for (const sceneKey of selectedScenes) {
        const container = containers[sceneKey];
        if (!container) continue;
        
        const rect = container.getBoundingClientRect();
        const name = SCENES[sceneKey].name;

        try {
            const dataUrl = await htmlToImage.toPng(container, {
                width: rect.width,
                height: rect.height,
                useCORS: true,
                allowTaint: true,
                pixelRatio: window.devicePixelRatio
            });
            
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = `${name}.png`;
            link.click();
        } catch (error) {
            console.error('Error capturing screenshot:', error);
            alert(`截图失败: ${error.message}`);
        }
    }
}