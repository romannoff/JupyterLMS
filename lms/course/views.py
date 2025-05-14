from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
import datetime
import numpy as np

from course.models import Tasks, Courses
from users.models import Solution

from course.task import check_student_code
from course.src.logging_config import logger


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
    }
    solution = Solution.objects.filter(task=task, user=request.user).order_by('-timestamp').first()

    if request.method == 'POST':
        code = request.POST['code']
        logger.info(code)

        if not (solution and code == solution.user_code) and code:
            notebook = 'course_files/LMS.ipynb'
            user_id = request.user.id
            time = task.time
            memory = task.memory
            task_name = task.name
            logger.info([code, notebook, task.id, time, memory, user_id, task_name])

            # Вместо выполнения непосредственно в запросе, отправляем задачу в Celery
            result = check_student_code.apply_async(
                args=[code, notebook, '095f1c66-fec2-4f9e-a487-5a1e75e4b505', time, memory, user_id, task_name, task.id]
            )

            # Возвращаем сообщение об успехе, можно будет добавить async обработку результата
            context['text'] = "Код отправлен на обработку"

    context['code'] = solution
    best_solution = Solution.objects.filter(task=task, user=request.user).order_by('score').first()
    context['best_solution'] = best_solution
    return render(request, 'course/task.html', context)