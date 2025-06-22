from celery import shared_task
from course.models import Tasks
from course.src.check_code import NotebookChecker
from users.models import Solution
from django.utils import timezone
import numpy as np
from course.src.logging_config import logger


@shared_task
def check_student_code(student_code, notebook_filename, task_id, time_limit, memory_limit, user_id, solution_id, get_logs):
    nb_checker = NotebookChecker()

    # Проведение тестирования
    result = nb_checker.check_code(student_code, notebook_filename, task_id, time_limit, memory_limit, get_logs)

    task = Tasks.objects.get(numb_of_task=task_id)

    # записываем в бд и решения. закончившиеся ошибкой, иначе скрипт бесконечно ждет ответа для автообновления страницы
    # Создание решения

    time_ = result['time'] if result['time'] is not None else 0
    memory = result['memory'] if result['memory'] is not None else 0
    score = np.sqrt(time_**2 + memory**2)

    Solution.objects.create(
        numb_of_solution=solution_id,
        user_id=user_id,
        task=task,
        user_code=student_code,
        timestamp=timezone.now(),
        text=result['text'],    # можно хранить ошибки, чтобы они отображались при входе
        time=time_,
        memory=memory,
        score=score,
        status='success' if result['time'] is not None else 'error'
    )

    # Обработка результата
    if result['time'] is None or result['memory'] is None:
        return {'status': 'error', 'text': result['text']}

    return {'status': 'success', 'solution_id': solution_id}