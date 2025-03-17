from django.http import HttpResponse
from django.shortcuts import render

def index(request):

    context = {
        'content': 'Some Content',
        'title': 'Каталог лучших курсов в мире!!!!!',
        'courses': [
            {'name': 'Best course in the world!!!!1', 'status': 'uncomplited'},
            {'name': 'Best course in the world!!!!2', 'status': 'uncomplited'},
            {'name': 'Best course in the world!!!!3', 'status': 'uncomplited'},
            ],
    }

    return render(request, 'main/index.html', context)

def example(request):
    
    context = {
        'content': 'example page',
        'title': 'EXAMPLE'
    }

    return render(request, 'main/index.html', context)

