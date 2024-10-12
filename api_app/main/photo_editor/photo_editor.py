import base64
import os
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from rembg import remove
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# def remove_background(request):
#     if request.method == 'POST' and 'image' in request.FILES:
#         # Get the uploaded file
#         image_file = request.FILES['image']

#         # Save the uploaded file to a temporary location
#         temp_file_path = default_storage.save('temp_image.jpg', image_file)

#         # Open the saved image using PIL
#         input_image = Image.open(default_storage.path(temp_file_path))

#         # Process the image using rembg (remove the background)
#         output_image = remove(
#             input_image,
#             alpha_matting=True,
#             alpha_matting_foreground_threshold=240,
#             post_process_mask=True,
#             alpha_matting_background_threshold=100,
#             alpha_matting_erode_structure_size=5,
#             alpha_matting_erode_size=11,
#             alpha_matting_base_size=1000,
#         )

#         # Convert the processed image to BytesIO for HTTP response
#         img_byte_arr = BytesIO()
#         output_image.save(img_byte_arr, format='PNG')  # Save as PNG to preserve transparency
#         img_byte_arr.seek(0)

#         # Serve the processed image as a downloadable response
#         response = HttpResponse(img_byte_arr, content_type='image/png')
#         response['Content-Disposition'] = 'attachment; filename="processed_image.png"'

#         # Clean up: Delete the temporary file
#         default_storage.delete(temp_file_path)

#         return response

#     return render(request, 'photo_editor/photo_editor.html')

def remove_background(request):
    return render(request, 'photo_editor/image_editor.html')


@require_POST
def remove_bg(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        threshold = request.POST['threshold']
        print('--------------- request ---------------', image)
        
        if image:
            # Process the image
            input_image = Image.open(image)

            if threshold == '0':
                output_image = remove(input_image)
                print('--------------- threshold == 0 ---------------', threshold)
            else:
                print('--------------- threshold != 0 ---------------', threshold)
                output_image = remove(
                    input_image,
                    # alpha_matting=True,
                    alpha_matting_foreground_threshold=f'{threshold}',
                    post_process_mask=True,
                    # alpha_matting_background_threshold=100,
                    # alpha_matting_erode_structure_size=5,
                    # alpha_matting_erode_size=11,
                    # alpha_matting_base_size=1000,
                )

            # Get bounding box of the object
            bbox = output_image.getbbox()
            if bbox:
                # Crop the image to the bounding box
                output_image = output_image.crop(bbox)
            
            # Save the processed image to an in-memory bytes buffer
            buffer = BytesIO()
            output_image.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Encode the image as base64
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

            # Construct the base64 string to be used in the frontend
            image_data_url = f"data:image/png;base64,{image_base64}"
            
            return JsonResponse({
                    'success': True, 
                    'imgName': f'{image}',
                    'image_data_url': image_data_url,
                    'range': 5, #range(5),
                })

    return JsonResponse({'success': False, 'error': 'Image processing failed'})


async def mirror_image(request):

    if request.method == 'POST':
        # Check if the image is part of the request
        if not request.FILES:
            return JsonResponse({"error": "Please provide an image."}, status=400)

        image_file = request.FILES['image']
        print('********* mirror_image **********', image_file)
        original_image = Image.open(image_file)

        # Flip the image vertically
        flipped_image = original_image.transpose(Image.FLIP_TOP_BOTTOM)

        # Get dimensions of the original image
        width, height = original_image.size

        # Create a new blank image with the combined height
        combined_image = Image.new('RGBA', (width, height * 2))

        # Paste the original image on the top
        combined_image.paste(original_image, (0, 0))

        # Paste the flipped image on the bottom
        combined_image.paste(flipped_image, (0, height))
        combined_image.show()

        # Save the combined image to a BytesIO object
        buffer = BytesIO()
        combined_image.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Encode the image as base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        # Construct the base64 string to be used in the frontend
        image_data_url = f"data:image/png;base64,{image_base64}"

        return JsonResponse({
            'success': True, 
            'imgName': f'{image_file}',  # Using name for clarity
            'image_data_url': image_data_url,
            'range': 5,  # Example static value
        })
    else:
        return JsonResponse({"error": "Invalid method."}, status=405)