from django.shortcuts import render, redirect

def invalid_token(request, name):
    return render(request, 'invalid_token.html', {'name': name})