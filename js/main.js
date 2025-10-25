// 主应用程序逻辑

// 全局变量
let allPoints = { scene1: [], scene2: [], scene3: [], scene4: [] };
let allItemLists = { scene1: [], scene2: [], scene3: [], scene4: [] };
let sceneRotations = { scene1: 0, scene2: 0, scene3: 0, scene4: 0 };
let resizeTimeout;
let globalXDirection = 'x+';
let globalYDirection = 'y-';
let globalReverseXY = false;

// DOM元素引用
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

// 事件监听器
window.addEventListener('resize', debounce(function() {
    if (jsonInput.value) {
        parseAndMarkPoints();
    }
}, 250));

window.addEventListener('resize', initCanvases);

// 主要功能函数
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
    } catch (error) {
        console.error('解析错误:', error);
        showError("解析错误: " + error.message);
    }
}

// 解析输入文本
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

// 获取选中的场景
function getSelectedScenes() {
    const checkboxes = document.querySelectorAll('.scene-checkboxes input[type="checkbox"]');
    return Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
}

// 应用场景到地图
function applySceneToMap(sceneKey) {
    const selectedScene = SCENES[sceneKey];
    if (selectedScene && images[sceneKey]) {
        images[sceneKey].src = selectedScene.imagePath;
    }
}

// 设置方向
function setDirection(newXDirection, newYDirection) {
    globalXDirection = newXDirection;
    globalYDirection = newYDirection;
    parseAndMarkPoints();
}

// 清除场景物品列表
function clearItemListsForScene(sceneKey) {
    containers[sceneKey].querySelectorAll('.item-list').forEach(item => item.remove());
    containers[sceneKey].querySelectorAll('.connection-line').forEach(line => line.remove());
    if (magneticGuides[sceneKey]) {
        magneticGuides[sceneKey].remove();
        magneticGuides[sceneKey] = null;
    }
    allPoints[sceneKey] = [];
    allItemLists[sceneKey] = [];
}

// 清除所有
function clearAll() {
    Object.keys(canvases).forEach(key => {
        const ctx = canvases[key].getContext('2d');
        ctx.clearRect(0, 0, canvases[key].width, canvases[key].height);
        clearItemListsForScene(key);
    });
}

// 旋转场景
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

// 重置旋转
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

// 截图功能
async function captureScreenshots() {
    if (window.location.protocol === 'file:') {
        alert('截图功能在file://协议下不可用，请使用以下方法之一：\n\n1. 使用Python HTTP服务器：\n   python -m http.server\n\n使用http://localhost:8000访问此页面。2. 使用Github page部署的网页');
        return;
    }

    const containers = document.querySelectorAll('.container');
    for (let i = 0; i < containers.length; i++) {
        const container = containers[i];
        const rect = container.getBoundingClientRect();
        const name = SCENES[`scene${i+1}`].name;

        htmlToImage.toPng(container, {
            width: rect.width,
            height: rect.height,
            useCORS: true,
            allowTaint: true,
            pixelRatio: window.devicePixelRatio
        })
        .then(function (dataUrl) {
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = `${name}.png`;
            link.click();
        })
        .catch(function (error) {
            console.error('Error capturing screenshot:', error);
            alert('截图失败: ' + error.message);
        });
    }
}