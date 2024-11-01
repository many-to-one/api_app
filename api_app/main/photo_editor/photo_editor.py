import base64
import os
import uuid
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from ..api_service import sync_service
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

    name = request.user.username
    url = f'sale/offers'
    debug_name = 'set_offers (all_offers) 15'
    all_offers = sync_service.Offers(name)
    result = all_offers.get_(request, url, debug_name)
    offers_cont = []
    for offer in result['offers']:
        offers_cont.append({
            'id': offer['id'], 
            'name': offer['name'], 
            'primaryImage': offer['primaryImage']
        })
        print("############### remove_background offers result ##################", offer['id']) 
    context = {
        'offers': offers_cont,
        'name': name,
    }
    return render(request, 'photo_editor/image_editor.html', context)


@require_POST
def remove_bg(request):
    if request.method == "POST":
        print('################## remove bg POST body #################', request)
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

from django.core.files.base import ContentFile
# @csrf_exempt
def mirror_image(request):
    if request.method == "POST":
        try:
            img_data = request.FILES.get("image")  # Retrieve image file from FormData
            if not img_data:
                return JsonResponse({"error": "No image file provided"}, status=400)

            # Generate a unique file name and save it
            file_name = f"{uuid.uuid4()}.jpeg"  # Use the correct extension based on image format
            file_path = default_storage.save(f"{file_name}", ContentFile(img_data.read()))

            # Return the full URL of the saved image
            image_url = request.build_absolute_uri(f"/media/{file_name}")
            return JsonResponse({"image_url": image_url}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)