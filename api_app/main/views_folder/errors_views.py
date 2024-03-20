from django.shortcuts import render, redirect

def invalid_token(request):
    return render(request, 'invalid_token.html')