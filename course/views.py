from django.shortcuts import render
from course.src.check_code import check_code

# Создаем подключение к Redis
# client = redis.StrictRedis(host='localhost', port=6379, db=0)


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
    context = {
        'title': 'Лучшее задание в мире!!!!!!!!!!!',
        'description': '''
        def my_fun(a, b):\n
            return a + b'''
    }
    if request.method == 'POST':
        code = request.POST['code']
        result = check_code(code)
        print(result)

        context['code'] = result['text']
        context['time'] = result['time']
        context['memory'] = result['memory']

    return render(request, 'course/task.html', context)
