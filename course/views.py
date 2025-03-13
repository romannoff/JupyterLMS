import re
from django.shortcuts import render

# Create your views here.

def subject(request):
    
    context = {
        'title': 'Список заданий лучшего курса в мире!!!',
        'tasks': [
            {'name': 'Best task in the world!!! 1', 'status': 'uncomplited'}, 
            {'name': 'Best task in the world!!! 2', 'status': 'uncomplited'}, 
            {'name': 'Best task in the world!!! 3', 'status': 'uncomplited'}
            ],
    }
    return render(request, 'course/subject.html', context)

def task(request):

    
    code = request.GET.get('code',"Your code")

    context = {
        'title': 'Лучшее задание в мире!!!!!!!!!!!',
        'description': 'Best description in the world!!!!!!',
        'code': code,
    }
    

    return render(request, 'course/task.html', context)