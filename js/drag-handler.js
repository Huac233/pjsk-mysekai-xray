// 拖拽处理功能

let magneticGuides = { scene1: null, scene2: null, scene3: null, scene4: null };

// 设置可拖拽物品列表
function setupDraggableItemList(itemList, sceneKey) {
    let isDragging = false;
    let startX, startY;
    let initialX, initialY;
    
    itemList.addEventListener('mousedown', startDrag);
    itemList.addEventListener('touchstart', startDrag, { passive: false });
    
    function startDrag(e) {
        e.preventDefault();
        isDragging = true;
        
        const rect = itemList.getBoundingClientRect();
        initialX = parseFloat(itemList.style.left) || 0;
        initialY = parseFloat(itemList.style.top) || 0;
        
        if (e.type === 'mousedown') {
            startX = e.clientX;
            startY = e.clientY;
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDrag);
        } else {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            document.addEventListener('touchmove', drag, { passive: false });
            document.addEventListener('touchend', stopDrag);
        }
        
        itemList.classList.add('dragging');
        hideMagneticGuides(sceneKey);
    }
    
    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        
        let currentX, currentY;
        if (e.type === 'mousemove') {
            currentX = e.clientX;
            currentY = e.clientY;
        } else {
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        }
        
        const dx = currentX - startX;
        const dy = currentY - startY;
        
        const rotation = sceneRotations[sceneKey];
        const adjustedDx = applyRotationToVector(dx, dy, rotation).x;
        const adjustedDy = applyRotationToVector(dx, dy, rotation).y;
        
        let newX = initialX + adjustedDx;
        let newY = initialY + adjustedDy;
        
        const magneticResult = applyMagneticEffect(sceneKey, newX, newY, itemList);
        newX = magneticResult.x;
        newY = magneticResult.y;
        
        const container = containers[sceneKey].querySelector('.image-container');
        const containerRect = container.getBoundingClientRect();
        const itemRect = itemList.getBoundingClientRect();
        
        const maxX = containerRect.width - itemRect.width;
        const maxY = containerRect.height - itemRect.height;
        
        newX = Math.max(0, Math.min(newX, maxX));
        newY = Math.max(0, Math.min(newY, maxY));
        
        itemList.style.left = `${newX}px`;
        itemList.style.top = `${newY}px`;
        
        updateItemListPosition(sceneKey, itemList, newX, newY);
        updateConnectionLinesForItemList(sceneKey, itemList);
    }
    
    function stopDrag() {
        isDragging = false;
        itemList.classList.remove('dragging');
        hideMagneticGuides(sceneKey);
        
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', stopDrag);
        document.removeEventListener('touchmove', drag);
        document.removeEventListener('touchend', stopDrag);
    }
}

// 应用磁吸效果
function applyMagneticEffect(sceneKey, x, y, itemList) {
    const magneticDistance = 10;
    let newX = x;
    let newY = y;
    
    const otherItemLists = Array.from(containers[sceneKey].querySelectorAll('.item-list')).filter(item => item !== itemList);
    
    for (const otherItem of otherItemLists) {
        const otherRect = otherItem.getBoundingClientRect();
        const itemRect = itemList.getBoundingClientRect();
        
        if (Math.abs((x + itemRect.width/2) - (parseFloat(otherItem.style.left) + otherRect.width/2)) < magneticDistance) {
            newX = parseFloat(otherItem.style.left) + (otherRect.width - itemRect.width)/2;
            showMagneticGuide(sceneKey, 'vertical', parseFloat(otherItem.style.left) + otherRect.width/2);
        }
        
        if (Math.abs((y + itemRect.height/2) - (parseFloat(otherItem.style.top) + otherRect.height/2)) < magneticDistance) {
            newY = parseFloat(otherItem.style.top) + (otherRect.height - itemRect.height)/2;
            showMagneticGuide(sceneKey, 'horizontal', parseFloat(otherItem.style.top) + otherRect.height/2);
        }
    }
    
    const container = containers[sceneKey].querySelector('.image-container');
    const containerRect = container.getBoundingClientRect();
    const itemRect = itemList.getBoundingClientRect();
    
    if (Math.abs(x) < magneticDistance) {
        newX = 0;
        showMagneticGuide(sceneKey, 'vertical', 0);
    }
    
    if (Math.abs(y) < magneticDistance) {
        newY = 0;
        showMagneticGuide(sceneKey, 'horizontal', 0);
    }
    
    if (Math.abs(containerRect.width - (x + itemRect.width)) < magneticDistance) {
        newX = containerRect.width - itemRect.width;
        showMagneticGuide(sceneKey, 'vertical', containerRect.width);
    }
    
    if (Math.abs(containerRect.height - (y + itemRect.height)) < magneticDistance) {
        newY = containerRect.height - itemRect.height;
        showMagneticGuide(sceneKey, 'horizontal', containerRect.height);
    }
    
    return { x: newX, y: newY };
}

// 显示磁吸引导线
function showMagneticGuide(sceneKey, type, position) {
    if (!magneticGuides[sceneKey]) {
        magneticGuides[sceneKey] = document.createElement('div');
        magneticGuides[sceneKey].className = 'magnetic-guides';
        containers[sceneKey].querySelector('.image-container').appendChild(magneticGuides[sceneKey]);
    }
    
    const guide = document.createElement('div');
    guide.className = `magnetic-guide ${type}`;
    
    if (type === 'horizontal') {
        guide.style.top = `${position}px`;
        guide.style.left = '0';
        guide.style.width = '100%';
    } else {
        guide.style.left = `${position}px`;
        guide.style.top = '0';
        guide.style.height = '100%';
    }
    
    magneticGuides[sceneKey].appendChild(guide);
}

// 隐藏磁吸引导线
function hideMagneticGuides(sceneKey) {
    if (magneticGuides[sceneKey]) {
        magneticGuides[sceneKey].innerHTML = '';
    }
}

// 更新物品列表位置
function updateItemListPosition(sceneKey, itemList, x, y) {
    const points = allPoints[sceneKey];
    for (const point of points) {
        if (point.itemList === itemList) {
            point.itemListX = x;
            point.itemListY = y;
            point.itemListWidth = itemList.offsetWidth;
            point.itemListHeight = itemList.offsetHeight;
            break;
        }
    }
}

// 更新连接线
function updateConnectionLinesForItemList(sceneKey, itemList) {
    const points = allPoints[sceneKey];
    for (const point of points) {
        if (point.itemList === itemList && point.connectionLine) {
            updateConnectionLine(point);
        }
    }
}

function updateConnectionLine(point) {
    if (!point.connectionLine) return;
    
    const startX = point.x;
    const startY = point.y;
    
    const endX = point.itemListX + point.itemListWidth / 2;
    const endY = point.itemListY + point.itemListHeight / 2;
    
    const dx = endX - startX;
    const dy = endY - startY;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    point.connectionLine.style.width = `${length}px`;
    point.connectionLine.style.transform = `rotate(${angle}deg)`;
}