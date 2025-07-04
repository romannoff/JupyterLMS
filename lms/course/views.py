from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
import uuid
from django.utils.safestring import mark_safe

from course.models import Tasks, Courses
from users.models import Solution

from course.task import check_student_code
from course.src.logging_config import logger


@login_required
def subject(request, subject_slug):

    course = Courses.objects.get(slug=subject_slug)
    course_name = course.name
    tasks = Tasks.objects.filter(course=course)
    task_n_mask = []
    for task in tasks:
        task_n_mask.append([task, 1 - (Solution.objects.filter(task=task.id, user=request.user.id, status='success').first() is None)])     
    

    context = {
        'title': 'Список заданий курса',
        'tasks': task_n_mask,
        'course_name': course_name,
    }
    return render(request, 'course/subject.html', context)

@login_required
def task(request, task_slug):

    # Сюда кинь флаг
    get_logs = False

    task = Tasks.objects.get(slug=task_slug)
    context = {
        'title': task,
        'description': mark_safe(task.description),
        'task_slug': task_slug,
    }
    solution = Solution.objects.filter(task=task.id, user=request.user.id).order_by('-timestamp').first()

    if solution:
        context['text'] = solution.text
        context['code'] = solution

    if request.method == 'POST':
        code = request.POST['code']
        context['code'] = None
        context['user_code'] = code
        logger.info(code)

        if not (solution and code == solution.user_code) and code:
            notebook = 'course_files/' + task.course.notebook.name
            user_id = request.user.id
            time = task.time
            memory = task.memory
            task_name = task.name
            task_id = task.numb_of_task
            solution_id = uuid.uuid4()
            logger.info([code, notebook, task_id, time, memory, user_id, task_name, get_logs])

            # Вместо выполнения непосредственно в запросе, отправляем задачу в Celery
            check_student_code.apply_async(
                args=[code, notebook, task_id, time, memory, user_id, solution_id, get_logs]
            )

            # Возвращаем сообщение об успехе, можно будет добавить async обработку результата
            context['text'] = "Код отправлен на обработку"
            context['solution_id'] = solution_id

    best_solution = Solution.objects.filter(task=task.id, user=request.user.id, status='success').order_by('score').first()
    context['best_solution'] = best_solution
    return render(request, 'course/task.html', context)

@login_required
def check_status(request, task_slug, solution_id):
    try:
        code_check = Solution.objects.get(numb_of_solution=solution_id)
        return JsonResponse({'status': code_check.status})
    except Solution.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)