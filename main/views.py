from django.http import HttpResponse
from django.shortcuts import render

def index(request):

    context = {
        'content': 'Some Content',
        'title': 'Каталог лучших курсов в мире!!!!!'
    }

    return render(request, 'main/index.html', context)

def example(request):
    
    context = {
        'content': 'example page',
        'title': 'EXAMPLE'
    }

    return render(request, 'main/index.html', context)

