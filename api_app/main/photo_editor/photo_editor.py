import base64
import os
import uuid
from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from django.core.files.storage import default_storage

from ..task import process_image
from ..api_service import sync_service
from rembg import remove, new_session
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import io, sys, subprocess

from celery.result import AsyncResult



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



# Set the model globally
session = new_session(model_name='u2netp')
MAX_SIZE_KB = 500  # Target size in KB
TARGET_BYTES = MAX_SIZE_KB * 1024  # Convert to bytes


@require_POST
def remove_bg(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        threshold = request.POST['threshold']
        
        if image:
            # Read image data as bytes
            image_data = image.read()
            
            # Trigger Celery task
            task = process_image.delay(image_data, threshold)

            print('************** TASK ID ****************', task.id)

            if task:
                return JsonResponse({
                    'success': True, 
                    'imgName': f'{image}',
                    'image_data_url': task.id,
                    'range': 5, #range(5),
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'imgName': f'{image}',
                    'image_data_url': task.id,
                    'range': 5, #range(5),
                })


            # # Return task ID to the client
            # return JsonResponse({
            #         'success': True, 
            #         'imgName': f'{image}',
            #         'image_data_url': task,
            #         'range': 5, #range(5),
            #     })

    return JsonResponse({'success': False, 'error': 'Image processing failed'})

def get_rembg_status(request, id):
    task = AsyncResult(id)

    if task.state == 'PENDING':
        # Task is still processing
        return JsonResponse({'status': 'PENDING', 'image_data_url': 'In progress...'})

    if task.state == 'SUCCESS':
        # Task completed successfully, return the result
        return JsonResponse({'status': 'SUCCESS', 'image_data_url': task.result})

    if task.state == 'FAILURE':
        # Task failed
        return JsonResponse({'status': 'FAILURE', 'image_data_url': str(task.info)})

    return JsonResponse({'status': 'UNKNOWN', 'image_data_url': 'Unknown task state'})

# @require_POST
# def remove_bg(request):
#     if request.method == "POST":
#         print('################## remove bg POST body #################', request)
#         image = request.FILES.get("image")
#         threshold = request.POST['threshold']
#         print('--------------- request ---------------', image)
        
#         if image:
#              # Process the image
#             input_image_ = Image.open(image)
#             # Check image size and format
#             width, height = input_image_.size  # Dimensions (width, height)
#             format = input_image_.format       # Format (e.g., 'JPEG', 'PNG')
#             file_size_kb = image.size / 1024  # File size in KB

#             new_width = width // 2
#             new_height = height // 2
#             input_image = input_image_.resize((new_width, new_height))

#             print(f'Image dimensions: {width}x{height}')
#             print(f'Image format: {format}')
#             print(f'Image file size: {file_size_kb:.2f} KB')

#             if threshold == '0':
#                 # output_image = remove(input_image, session=session)
#                 output_image = remove(input_image)
#                 print('--------------- threshold == 0 ---------------', threshold)
#             else:
#                 print('--------------- threshold != 0 ---------------', threshold)
#                 output_image = remove(
#                     input_image,
#                      alpha_matting=True,
#                     alpha_matting_foreground_threshold=f'{threshold}',
#                     post_process_mask=True,
#                      alpha_matting_background_threshold=100,
#                      alpha_matting_erode_structure_size=5,
#                      alpha_matting_erode_size=11,
#                      alpha_matting_base_size=1000,
#                 )

#             # Get bounding box of the object
#             bbox = output_image.getbbox()
#             if bbox:
#                  # Crop the image to the bounding box
#                 output_image = output_image.crop(bbox)
            
#             # Save the processed image to an in-memory bytes buffer
#             buffer = io.BytesIO()
#             output_image.save(buffer, format="PNG")
#             buffer.seek(0)

#             # Encode the image as base64
#             image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

#             # Construct the base64 string to be used in the frontend
#             image_data_url = f"data:image/png;base64,{image_base64}"

#             # Calculate the size of image_data_url in bytes
#             image_data_url_size = sys.getsizeof(image_data_url)

#             # print('************* SUCCESS ***************', image_data_url)
#             print(f'Size of image_data_url: {image_data_url_size} bytes')
#             return JsonResponse({
#                     'success': True, 
#                     'imgName': f'{image}',
#                     'image_data_url': image_data_url,
#                     'range': 5, #range(5),
#                 })

#     return JsonResponse({'success': False, 'error': 'Image processing failed'})




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
