from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout


def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        # CLIENT_ID = request.POST.get('CLIENT_ID')
        # CLIENT_SECRET = request.POST.get('CLIENT_SECRET')


        try:
            user = CustomUser.objects.create(
                email=email,
                username=username,
                # CLIENT_ID=CLIENT_ID,
                # CLIENT_SECRET=CLIENT_SECRET,
            )
            user.set_password(password)
            user.save()

            if user:
                return JsonResponse({
                    'message': 'success',
                    'username': username,
                })
            else:
                pass
        except Exception as e:
            pass

    return render(request, 'register.html')


def login_user(request):
    if request.method == 'POST':
        # Retrieve form data
        email = request.POST.get('email')
        password = request.POST.get('password')

        # print('EMAIL -----', email)
        # print('PASSWORD -----', password)

        # if email:
        #     return JsonResponse({'message': 'email'})

        # Authenticate user
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # User authentication successful, log the user in
            login(request, user)
            return JsonResponse({'message': 'Login successful'})
        else:
            # User authentication failed, return an error message
            return JsonResponse({'error': 'Invalid credentials'}, status=400)

    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    # Redirect to a specific URL after logout, or to the homepage
    return redirect('index')
