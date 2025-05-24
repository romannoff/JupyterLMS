from celery import shared_task
from course.models import Tasks
from course.src.check_code import NotebookChecker
from users.models import Solution
from django.utils import timezone
import numpy as np
from course.src.logging_config import logger


@shared_task
def check_student_code(student_code, notebook_filename, task_id, time_limit, memory_limit, user_id, solution_id):
    nb_checker = NotebookChecker()

    # Проведение тестирования
    result = nb_checker.check_code(student_code, notebook_filename, task_id, time_limit, memory_limit)

    task = Tasks.objects.get(numb_of_task=task_id)

    # записываем в бд и решения. закончившиеся ошибкой, иначе скрипт бесконечно ждет ответа для автообновления страницы
    # Создание решения
    Solution.objects.create(
        numb_of_solution=solution_id,
        user_id=user_id,
        task=task,
        user_code=student_code,
        timestamp=timezone.now(),
        text=result['text'],    # можно хранить ошибки, чтобы они отображались при входе
        time=result['time'],
        memory=result['memory'],
        score=np.sqrt(result['time'] ** 2 + result['memory'] ** 2) if result['time'] is not None else 0,
        status='success' if result['time'] is not None else 'error' # статус решения, нужен для автообновления странички. может принимать 2 значения: 'success' или 'error'
        # time=float(result['time'].split('#')[0]),
        # memory=float(result['memory'].split('#')[0]),
        # score=np.sqrt(float(result['time'].split('#')[0]) ** 2 + float(result['memory'].split('#')[0]) ** 2)
    )

    # Обработка результата
    if result['time'] is None or result['memory'] is None:
        return {'status': 'error', 'text': result['text']}

    return {'status': 'success', 'solution_id': solution_id}