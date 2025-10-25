// 网格渲染功能

// 初始化画布
function initCanvases() {
    Object.keys(canvases).forEach(key => {
        const canvas = canvases[key];
        const image = images[key];
        if (image && canvas) {
            canvas.width = image.clientWidth;
            canvas.height = image.clientHeight;
        }
    });
}

// 绘制所有网格
function drawGrids() {
    Object.keys(SCENES).forEach(key => {
        applySceneToMap(key);
        drawGridForScene(key);
    });
}

// 绘制场景网格
function drawGridForScene(sceneKey) {
    const canvas = canvases[sceneKey];
    const ctx = canvas.getContext('2d');
    const image = images[sceneKey];
    const scene = SCENES[sceneKey];
    const physicalGridWidth = scene.physicalWidth;
    const offsetX = scene.offsetX;
    const offsetY = scene.offsetY;
    const displayWidth = image.clientWidth;
    const displayHeight = image.clientHeight;
    const naturalWidth = image.naturalWidth;
    const naturalHeight = image.naturalHeight;
    const scaleX = displayWidth / naturalWidth;
    const scaleY = displayHeight / naturalHeight;
    const displayGridWidth = physicalGridWidth * scaleX;
    const originX = displayWidth / 2 + offsetX;
    const originY = displayHeight / 2 + offsetY;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(255, 0, 0, 0.3)';
    ctx.lineWidth = 1;

    for (let y = originY; y >= 0; y -= displayGridWidth) {
        drawHorizontalLine(ctx, y, canvas.width);
    }
    for (let y = originY + displayGridWidth; y <= displayHeight; y += displayGridWidth) {
        drawHorizontalLine(ctx, y, canvas.width);
    }
    for (let x = originX; x >= 0; x -= displayGridWidth) {
        drawVerticalLine(ctx, x, canvas.height);
    }
    for (let x = originX + displayGridWidth; x <= displayWidth; x += displayGridWidth) {
        drawVerticalLine(ctx, x, canvas.height);
    }

    drawCoordinateAxes(ctx, originX, originY);
}

// 绘制水平线
function drawHorizontalLine(ctx, y, width) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
}

// 绘制垂直线
function drawVerticalLine(ctx, x, height) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
}

// 绘制坐标轴
function drawCoordinateAxes(ctx, originX, originY) {
    const crossSize = 3;
    ctx.strokeStyle = 'black';
    ctx.beginPath();
    ctx.moveTo(originX - crossSize, originY - crossSize);
    ctx.lineTo(originX + crossSize, originY + crossSize);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(originX + crossSize, originY - crossSize);
    ctx.lineTo(originX - crossSize, originY + crossSize);
    ctx.stroke();
}