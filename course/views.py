from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
import datetime
import numpy as np

from course.models import Tasks, Courses
from users.models import Solution

from src.check_code import NotebookChecker
from src.logging_config import logger

nb_checker = NotebookChecker()


@login_required
def subject(request, subject_slug):

    course = Courses.objects.get(slug=subject_slug)
    course_name = course.name
    tasks = Tasks.objects.filter(course=course)
    

    context = {
        'title': 'Список заданий курса',
        'tasks': tasks,
        'course_name': course_name,
    }
    return render(request, 'course/subject.html', context)

@login_required
def task(request, task_slug):
    task = Tasks.objects.get(slug=task_slug)
    context = {
        'title': task,
        'description': task.description,
    }
    solution = Solution.objects.filter(task=task, user=request.user).order_by('-timestamp').first()

    if request.method == 'POST':
        code = request.POST['code']
        print(code)


        if not (solution and code == solution.user_code) and code:

            notebook = task.notebook # расположение ноутбука с тестами
            logger.info(code)
            result = nb_checker.check_code(code)
            logger.info(result)

            if result['time'] is None or result['memory'] is None:
                context['text'] = result['text']
                context['code'] = code
            else:
                solution = Solution.objects.create(
                    user=request.user, 
                    task=task, 
                    user_code=code, 
                    timestamp=datetime.datetime.now(), 
                    time=float(result['time'].split('#')[0]), 
                    memory=float(result['memory'].split('#')[0]),
                    score = np.sqrt(float(result['time'].split('#')[0])**2 + float(result['memory'].split('#')[0])**2)
                    )
                context['code'] = solution

        # items = render_to_string('course/task.html', context, request=request)
        # return JsonResponse({'items' : items})
    best_solution = Solution.objects.filter(task=task, user=request.user).order_by('score').first()
    context['best_solution'] = best_solution
    return render(request, 'course/task.html', context)
