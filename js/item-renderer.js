// 物品渲染功能

// 创建物品列表
function createItemList(reward, ifContainRareItem, ifContainSuperRareItem, sceneKey) {
    const itemList = document.createElement('div');
    itemList.className = 'item-list';

    for (const category in reward) {
        if (!reward.hasOwnProperty(category)) continue;
        for (const itemId in reward[category]) {
            if (!reward[category].hasOwnProperty(itemId)) continue;
            const quantity = reward[category][itemId];
            let texture;
            
            if (category === "mysekai_music_record") {
                texture = getMusicRecordUrl(itemId);
            } else {
                texture = ITEM_TEXTURES[category]?.[itemId] || 'missing.png';
            }

            const itemEntry = document.createElement('div');
            const itemImage = document.createElement('img');
            let retryCount = 0;
            const maxRetries = PROXY_CONFIG.proxies.length;

            const loadImage = (useProxy = false) => {
                if (category === "mysekai_music_record") {
                    const recordData = MUSIC_RECORD_MAPPING[itemId];
                    if (!recordData) {
                        itemImage.src = './icon/Texture2D/item_surplus_music_record.png';
                        return;
                    }
                    const { external_id, server } = recordData;
                    const numId = parseInt(external_id);
                    const formattedId = numId < 100 ? String(numId).padStart(3, '0') : String(numId);
                    const originalUrl = `https://storage.sekai.best/sekai-${server}-assets/music/jacket/jacket_s_${formattedId}/jacket_s_${formattedId}.png`;
                    
                    if (useProxy && retryCount < maxRetries) {
                        const proxyUrl = PROXY_CONFIG.proxies[retryCount];
                        itemImage.src = proxyUrl + encodeURIComponent(originalUrl);
                    } else {
                        itemImage.src = originalUrl;
                    }
                } else {
                    itemImage.src = texture;
                }
            };

            loadImage(false);

            itemImage.onerror = function() {
                if (category === "mysekai_music_record" && retryCount < maxRetries) {
                    retryCount++;
                    loadImage(true);
                } else {
                    this.src = (category === "mysekai_music_record") 
                        ? './icon/Texture2D/item_surplus_music_record.png' 
                        : 'missing.png';
                }
            };

            const quantityBadge = document.createElement('span');
            quantityBadge.className = 'quantity';
            quantityBadge.textContent = quantity;
            itemEntry.style.position = 'relative';
            itemEntry.style.display = 'inline-block';
            itemEntry.style.margin = '1px';
            itemEntry.appendChild(itemImage);
            itemEntry.appendChild(quantityBadge);
            itemList.appendChild(itemEntry);  
        }
    }

    if (ifContainSuperRareItem) {
        itemList.style.background = 'rgba(255, 0, 0, 0.5)';
        itemList.style.zIndex = '20';
    } else if (ifContainRareItem || reward.hasOwnProperty("mysekai_music_record")) {
        itemList.style.background = 'rgba(0, 0, 180, 0.5)';
        itemList.style.zIndex = '15';
    } else {
        itemList.style.zIndex = '10';
    }

    if (containers[sceneKey] && containers[sceneKey].querySelector('.image-container')) {
        containers[sceneKey].querySelector('.image-container').appendChild(itemList);
        allItemLists[sceneKey].push(itemList);
        
        itemList.style.transform = `rotate(${-sceneRotations[sceneKey]}deg)`;
        
        setupDraggableItemList(itemList, sceneKey);
    }
    
    return itemList;
}

// 标记场景点
function markPointForScene(sceneKey, point, xDir, yDir) {
    const canvas = canvases[sceneKey];
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const image = images[sceneKey];
    const scene = SCENES[sceneKey];
    const [x, y] = point.location;
    const offsetX = scene.offsetX;
    const offsetY = scene.offsetY;
    const originX = canvas.width / 2 + offsetX;
    const originY = canvas.height / 2 + offsetY;
    const displayGridWidth = scene.physicalWidth * (image.clientWidth / image.naturalWidth);
    const displayX = xDir === 'x+' ? originX + x * displayGridWidth : originX - x * displayGridWidth;
    const displayY = yDir === 'y+' ? originY + y * displayGridWidth : originY - y * displayGridWidth;
    const color = FIXTURE_COLORS[point.fixtureId];
    let ifContainRareItem = false;
    let ifContainSuperRareItem = false;

    if (color) {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(displayX, displayY, 5, 0, Math.PI * 2);
        ctx.fill();

        const containsRareItem = doContainsRareItem(point.reward, false);
        const containsSuperRareItem = doContainsRareItem(point.reward, true);
        
        if (containsRareItem || containsSuperRareItem) {
            ctx.strokeStyle = 'red';
            ifContainRareItem = containsRareItem;
            ifContainSuperRareItem = containsSuperRareItem;
        } else {
            ctx.strokeStyle = 'black';
        }
        ctx.beginPath();
        ctx.arc(displayX, displayY, 5, 0, Math.PI * 2);
        ctx.stroke();

        const itemList = createItemList(point.reward, ifContainRareItem, ifContainSuperRareItem, sceneKey);
        
        allPoints[sceneKey].push({
            x: displayX, 
            y: displayY, 
            itemList: itemList,
            isRare: ifContainRareItem || ifContainSuperRareItem,
            isSuperRare: ifContainSuperRareItem,
            reward: point.reward,
            connectionLine: null
        });
    } else {
        ctx.fillStyle = 'black';
        ctx.font = '12px Arial';
        ctx.fillText('?', displayX - 3, displayY + 4);
    }
}

// 检查是否包含稀有物品
function doContainsRareItem(reward, isSuperRare = false) {
    let compareList = isSuperRare ? SUPER_RARE_ITEM : RARE_ITEM;
    for (const category in reward) {
        if (reward.hasOwnProperty(category) && compareList.hasOwnProperty(category)) {
            for (const itemId of Object.keys(reward[category])) {
                if (compareList[category].includes(parseInt(itemId))) {
                    return true;
                }
            }
        }
    }
    return false;
}

// 优化物品列表位置
function optimizeItemListPositionsForScene(sceneKey) {
    const container = containers[sceneKey].querySelector('.image-container');
    const canvas = canvases[sceneKey];
    const points = allPoints[sceneKey];
    const containerRect = container.getBoundingClientRect();
    
    points.sort((a, b) => {
        if (a.isSuperRare && !b.isSuperRare) return -1;
        if (!a.isSuperRare && b.isSuperRare) return 1;
        if (a.isRare && !b.isRare) return -1;
        if (!a.isRare && b.isRare) return 1;
        return 0;
    });

    const placedBounds = [];
    const margin = 20;
    
    const quadrantCounts = { q1: 0, q2: 0, q3: 0, q4: 0 };
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    points.forEach(point => {
        const image = images[sceneKey];
        const scene = SCENES[sceneKey];
        const displayGridWidth = scene.physicalWidth * (image.clientWidth / image.naturalWidth);
        const itemList = point.itemList;
        
        itemList.style.display = 'block';
        const itemRect = itemList.getBoundingClientRect();
        const itemWidth = itemRect.width;
        const itemHeight = itemRect.height;
        
        const itemCount = Object.values(point.reward).reduce((sum, category) => 
            sum + Object.keys(category).length, 0);
        
        let baseDistance = Math.max(
            displayGridWidth * 1.8, 
            Math.max(itemWidth, itemHeight) * 0.8 + itemCount * 5
        );
        if (point.isRare || point.isSuperRare) {
            baseDistance *= 1.2;
        }
        
        let bestPosition = null;
        let bestScore = -Infinity;
        
        let startAngle = 0;
        if (point.x > centerX) {
            startAngle = 180;
        } else if (point.x < centerX) {
            startAngle = 0;
        }
        if (point.y > centerY) {
            startAngle += 90;
        } else if (point.y < centerY) {
            startAngle -= 90;
        }
        
        for (let distanceMultiplier = 0.8; distanceMultiplier <= 3.5; distanceMultiplier += 0.3) {
            for (let angleOffset = 0; angleOffset < 360; angleOffset += 15) {
                const angle = (startAngle + angleOffset) % 360;
                const rad = angle * Math.PI / 180;
                const testX = point.x + Math.cos(rad) * baseDistance * distanceMultiplier;
                const testY = point.y + Math.sin(rad) * baseDistance * distanceMultiplier;
                
                if (testX < 5 || testX > canvas.width - itemWidth - 5 ||
                    testY < 5 || testY > canvas.height - itemHeight - 5) {
                    continue;
                }
                
                const testBounds = {
                    left: testX,
                    top: testY,
                    right: testX + itemWidth,
                    bottom: testY + itemHeight,
                    width: itemWidth,
                    height: itemHeight
                };
                
                let score = 0;
                
                let hasOverlap = false;
                let overlapArea = 0;
                for (const placed of placedBounds) {
                    const overlap = getOverlapArea(testBounds, placed);
                    if (overlap > 0) {
                        overlapArea += overlap;
                        hasOverlap = true;
                    }
                }
                score -= overlapArea * 15;
                
                if (!hasOverlap) {
                    score += 1500;
                }
                
                const distanceToPoint = Math.sqrt(
                    Math.pow(testX - point.x, 2) + 
                    Math.pow(testY - point.y, 2)
                );
                const idealDistance = baseDistance * 1.2;
                score += 600 - Math.abs(distanceToPoint - idealDistance) * 2;
                
                let coverCount = 0;
                for (const otherPoint of points) {
                    if (otherPoint === point) continue;
                    
                    const pointInBox = (
                        otherPoint.x >= testBounds.left - 5 && 
                        otherPoint.x <= testBounds.right + 5 &&
                        otherPoint.y >= testBounds.top - 5 && 
                        otherPoint.y <= testBounds.bottom + 5
                    );
                    
                    if (pointInBox) {
                        coverCount++;
                    }
                }
                score -= coverCount * 600;
                
                const edgeMargin = 30;
                if (testX < edgeMargin || testX > canvas.width - itemWidth - edgeMargin ||
                    testY < edgeMargin || testY > canvas.height - itemHeight - edgeMargin) {
                    score -= 200;
                }
                
                let quadrant = 'q1';
                if (testX >= centerX && testY < centerY) quadrant = 'q1';
                else if (testX < centerX && testY < centerY) quadrant = 'q2';
                else if (testX < centerX && testY >= centerY) quadrant = 'q3';
                else if (testX >= centerX && testY >= centerY) quadrant = 'q4';
                
                const quadScore = (Math.max(0, 10 - quadrantCounts[quadrant]) * 100);
                score += quadScore;
                
                score -= distanceToPoint * 0.2;
                if (distanceToPoint > baseDistance * 2.5) {
                    score -= 300;
                }
                
                const dx = testX - point.x;
                const dy = testY - point.y;
                if (point.x > centerX && dx < 0) score += 100;
                if (point.x < centerX && dx > 0) score += 100;
                if (point.y > centerY && dy < 0) score += 100;
                if (point.y < centerY && dy > 0) score += 100;
                
                if (score > bestScore) {
                    bestScore = score;
                    bestPosition = { x: testX, y: testY, quadrant: quadrant };
                }
            }
        }
        
        if (bestPosition) {
            itemList.style.left = `${bestPosition.x}px`;
            itemList.style.top = `${bestPosition.y}px`;
            
            quadrantCounts[bestPosition.quadrant]++;
            
            point.itemListX = bestPosition.x;
            point.itemListY = bestPosition.y;
            point.itemListWidth = itemWidth;
            point.itemListHeight = itemHeight;
            
            placedBounds.push({
                left: bestPosition.x,
                top: bestPosition.y,
                right: bestPosition.x + itemWidth,
                bottom: bestPosition.y + itemHeight,
                width: itemWidth,
                height: itemHeight
            });
        } else {
            const defaultX = point.x - displayGridWidth * 1.5;
            const defaultY = point.y - displayGridWidth / 1.2;
            
            itemList.style.left = `${defaultX}px`;
            itemList.style.top = `${defaultY}px`;
            
            point.itemListX = defaultX;
            point.itemListY = defaultY;
            point.itemListWidth = itemWidth;
            point.itemListHeight = itemHeight;
            
            placedBounds.push({
                left: defaultX,
                top: defaultY,
                right: defaultX + itemWidth,
                bottom: defaultY + itemHeight,
                width: itemWidth,
                height: itemHeight
            });
        }
    });
    
    finalAdjustItemListsForScene(sceneKey);
}

// 最终调整物品列表位置
function finalAdjustItemListsForScene(sceneKey) {
    const itemLists = Array.from(containers[sceneKey].querySelectorAll('.item-list'));
    let adjusted;
    let iterations = 0;
    
    do {
        adjusted = false;
        iterations++;
        
        for (let i = 0; i < itemLists.length; i++) {
            for (let j = i + 1; j < itemLists.length; j++) {
                const rect1 = itemLists[i].getBoundingClientRect();
                const rect2 = itemLists[j].getBoundingClientRect();
                
                const overlapX = Math.min(rect1.right, rect2.right) - Math.max(rect1.left, rect2.left);
                const overlapY = Math.min(rect1.bottom, rect2.bottom) - Math.max(rect1.top, rect2.top);
                
                if (overlapX > 5 && overlapY > 5) {
                    adjusted = true;
                    
                    const center1 = {
                        x: rect1.left + rect1.width / 2,
                        y: rect1.top + rect1.height / 2
                    };
                    const center2 = {
                        x: rect2.left + rect2.width / 2,
                        y: rect2.top + rect2.height / 2
                    };
                    
                    const dx = center2.x - center1.x;
                    const dy = center2.y - center1.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance > 0) {
                        const moveDistance = Math.max(overlapX, overlapY) / 2 + 8;
                        const moveX = (dx / distance) * moveDistance;
                        const moveY = (dy / distance) * moveDistance;
                        
                        const currentLeft1 = parseFloat(itemLists[i].style.left);
                        const currentTop1 = parseFloat(itemLists[i].style.top);
                        const currentLeft2 = parseFloat(itemLists[j].style.left);
                        const currentTop2 = parseFloat(itemLists[j].style.top);
                        
                        itemLists[i].style.left = `${currentLeft1 - moveX}px`;
                        itemLists[i].style.top = `${currentTop1 - moveY}px`;
                        itemLists[j].style.left = `${currentLeft2 + moveX}px`;
                        itemLists[j].style.top = `${currentTop2 + moveY}px`;
                        
                        updateItemListPosition(sceneKey, itemLists[i], currentLeft1 - moveX, currentTop1 - moveY);
                        updateItemListPosition(sceneKey, itemLists[j], currentLeft2 + moveX, currentTop2 + moveY);
                    }
                }
            }
        }
    } while (adjusted && iterations < 30);
}

// 绘制连接线
function drawConnectionLinesForScene(sceneKey) {
    containers[sceneKey].querySelectorAll('.connection-line').forEach(line => line.remove());
    
    allPoints[sceneKey].forEach(point => {
        if (!point.itemListX || !point.itemListY) return;
        
        const startX = point.x;
        const startY = point.y;
        
        const endX = point.itemListX + point.itemListWidth / 2;
        const endY = point.itemListY + point.itemListHeight / 2;
        
        const dx = endX - startX;
        const dy = endY - startY;
        const length = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx) * 180 / Math.PI;
        
        const line = document.createElement('div');
        line.className = 'connection-line';
        
        const lineWidth = window.devicePixelRatio > 1 ? '3px' : '2px';
        line.style.width = `${length}px`;
        line.style.height = lineWidth;
        line.style.background = point.isSuperRare ? 'rgba(255, 0, 0, 0.7)' : 
                              point.isRare ? 'rgba(0, 0, 180, 0.7)' : 'rgba(0, 0, 0, 0.5)';
        line.style.left = `${startX}px`;
        line.style.top = `${startY}px`;
        line.style.transform = `rotate(${angle}deg)`;
        line.style.transformOrigin = '0 0';
        line.style.zIndex = '1';
        line.style.position = 'absolute';
        
        containers[sceneKey].querySelector('.image-container').appendChild(line);
        
        point.connectionLine = line;
    });
}