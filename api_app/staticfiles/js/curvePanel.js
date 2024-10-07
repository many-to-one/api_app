const canvasCP = document.getElementById('curveCanvas');
const ctxCP = canvasCP.getContext('2d');
const rgbSelect = document.getElementById('rgbSelect');

// Curve control points
let controlPoints = [{ x: 50, y: 450 }, { x: 450, y: 50 }];
let selectedPoint = null;
const curveChannel = {
    rgb: [],
    red: [],
    green: [],
    blue: []
};
let activeChannel = 'rgb';

// Event listeners for canvas interaction
canvasCP.addEventListener('mousedown', handleMouseDown);
canvasCP.addEventListener('mousemove', handleMouseMove);
canvasCP.addEventListener('mouseup', handleMouseUp);
rgbSelect.addEventListener('change', () => {
    activeChannel = rgbSelect.value;
    drawCurve();
});

function handleMouseDown(event) {
    const mousePos = getMousePos(canvasCP, event);
    selectedPoint = findSelectedPoint(mousePos);
    if (!selectedPoint) {
        // Add a new point if clicked on an empty space
        controlPoints.push(mousePos);
        selectedPoint = mousePos;
    }
    drawCurve();
}

function handleMouseMove(event) {
    if (!selectedPoint) return;
    const mousePos = getMousePos(canvasCP, event);
    selectedPoint.x = Math.min(Math.max(mousePos.x, 0), canvasCP.width); // Constrain within canvas bounds
    selectedPoint.y = Math.min(Math.max(mousePos.y, 0), canvasCP.height);
    drawCurve();
    console.log('handleMouseMove', mousePos)
}

function handleMouseUp() {
    selectedPoint = null;
}

// Get mouse position relative to canvas
function getMousePos(canvas, event) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
    };
}

// Find the control point near the mouse position
function findSelectedPoint(mousePos) {
    for (let point of controlPoints) {
        const distance = Math.sqrt((point.x - mousePos.x) ** 2 + (point.y - mousePos.y) ** 2);
        if (distance < 10) return point;
    }
    return null;
}

// Draw the curve and control points
function drawCurve() {
    ctxCP.clearRect(0, 0, canvasCP.width, canvasCP.height);

    // Draw the curve
    ctxCP.strokeStyle = 'black';
    ctxCP.lineWidth = 2;
    ctxCP.beginPath();
    ctxCP.moveTo(0, 500);

    // Use bezier curve or smooth curve to join control points
    for (let i = 0; i < controlPoints.length - 1; i++) {
        const cp1 = controlPoints[i];
        const cp2 = controlPoints[i + 1];
        ctxCP.bezierCurveTo(cp1.x, cp1.y, cp2.x, cp2.y, cp2.x, cp2.y);
    }
    ctxCP.stroke();

    // Draw control points
    controlPoints.forEach((point) => {
        ctxCP.beginPath();
        ctxCP.arc(point.x, point.y, 5, 0, 2 * Math.PI);
        ctxCP.fillStyle = 'red';
        ctxCP.fill();
        ctxCP.strokeStyle = 'black';
        ctxCP.stroke();
    });
}

// Apply curve adjustment based on the control points
function applyCurveAdjustment(imageData) {
    const data = imageData.data;
    const points = controlPoints.sort((a, b) => a.x - b.x);

    // Adjust pixels based on control points (simple interpolation for now)
    for (let i = 0; i < data.length; i += 4) {
        const brightness = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
        const curveValue = getCurveValue(brightness, points);

        // Apply curve adjustment to all RGB channels or specific channel
        if (activeChannel === 'rgb' || activeChannel === 'red') data[i] = Math.min(255, curveValue); // Red
        if (activeChannel === 'rgb' || activeChannel === 'green') data[i + 1] = Math.min(255, curveValue); // Green
        if (activeChannel === 'rgb' || activeChannel === 'blue') data[i + 2] = Math.min(255, curveValue); // Blue
    }
    return imageData;
}

// Get curve value based on control points (linear interpolation)
function getCurveValue(brightness, points) {
    // Example: Simple linear interpolation (can be replaced with bezier curves)
    const lower = points[0];
    const upper = points[1];
    return lower.y + ((brightness - lower.x) / (upper.x - lower.x)) * (upper.y - lower.y);
}

drawCurve();
