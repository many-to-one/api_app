// Get canvas and context
const imgElement = document.getElementsByClassName('imgElement_' + activeImage)[0]; 
console.log('imgElement inside curve', imgElement)
const canvas = document.getElementById('imageCanvas');
const ctx = canvas.getContext('2d');

canvas.width = imgElement.naturalWidth; // imgElement.naturalWidth;  // Use naturalWidth and naturalHeight for original dimensions
canvas.height = imgElement.naturalHeight;

// Load an image to the canvas (use a placeholder image)
const img = new Image();
img.src = imgElement.src;//'https://via.placeholder.com/500';
img.onload = function() {
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    updateCanvas(); // Initial draw with default values
};

// Get sliders
const brightnessSlider = document.getElementById('brightnessSlider');
const redSlider = document.getElementById('redSlider');
const greenSlider = document.getElementById('greenSlider');
const blueSlider = document.getElementById('blueSlider');

// Update the image on the canvas whenever sliders change
brightnessSlider.addEventListener('input', updateCanvas);
redSlider.addEventListener('input', updateCanvas);
greenSlider.addEventListener('input', updateCanvas);
blueSlider.addEventListener('input', updateCanvas);

function updateCanvas() {
    // Clear the canvas before redrawing the image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Get image data from the canvas
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    // Get slider values
    const brightnessFactor = parseFloat(brightnessSlider.value);
    console.log('brightnessFactor', brightnessFactor)
    const redFactor = parseFloat(redSlider.value);
    const greenFactor = parseFloat(greenSlider.value);
    const blueFactor = parseFloat(blueSlider.value);

    // Loop through each pixel and adjust RGB values
    for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.min(255, data[i] * redFactor * brightnessFactor); // Red
        data[i + 1] = Math.min(255, data[i + 1] * greenFactor * brightnessFactor); // Green
        data[i + 2] = Math.min(255, data[i + 2] * blueFactor * brightnessFactor); // Blue
    }

    // Put the updated image data back onto the canvas
    ctx.putImageData(imageData, 0, 0);
    imgElement.src = canvas.toDataURL();

    console.log('imgElement result inside curve', imgElement)
}
