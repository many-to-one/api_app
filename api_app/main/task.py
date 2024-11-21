from celery import shared_task
from rembg import remove
from PIL import Image
import io
import base64

@shared_task
def process_image(image_data, threshold):
    # Open image from bytes
    input_image_ = Image.open(io.BytesIO(image_data))

    # Resize image for faster processing
    width, height = input_image_.size
    new_width = width // 2
    new_height = height // 2
    input_image = input_image_.resize((new_width, new_height))

    # Process image with rembg
    if threshold == '0':
        output_image = remove(input_image)
    else:
        output_image = remove(
            input_image,
            alpha_matting=True,
            alpha_matting_foreground_threshold=int(threshold),
            post_process_mask=True,
            alpha_matting_background_threshold=100,
            alpha_matting_erode_structure_size=5,
            alpha_matting_erode_size=11,
            alpha_matting_base_size=1000,
        )

    # Crop to bounding box if applicable
    bbox = output_image.getbbox()
    if bbox:
        output_image = output_image.crop(bbox)

    # Save processed image to buffer
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode to base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"
