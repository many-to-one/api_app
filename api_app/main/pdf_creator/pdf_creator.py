from django.shortcuts import render



def pdf_creator(request):
    return render(request, 'pdf_creator/pdf_creator.html')