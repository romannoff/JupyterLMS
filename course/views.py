from django.shortcuts import render
from course.files.check_code import check_code

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

    is_code = False

    context = {
        'title': 'Лучшее задание в мире!!!!!!!!!!!',
        'description': 'Best description in the world!!!!!!',
    }
    if request.method == 'POST':
        code = request.POST['code']
        is_code = True
        check_code(code)

        time = '0.0'
        memory = '10kB'
        context['code'] = code
        context['time'] = time
        context['memory'] = memory

    context['is_code'] = is_code

    return render(request, 'course/task.html', context)