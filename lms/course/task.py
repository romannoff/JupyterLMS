from celery import shared_task
from course.src.check_code import NotebookChecker
from users.models import Solution
from django.utils import timezone
import numpy as np
from course.src.logging_config import logger


@shared_task
def check_student_code(student_code, notebook_filename, task_id, time_limit, memory_limit, user_id, task_name, task_id_):
    nb_checker = NotebookChecker()

    # Проведение тестирования
    result = nb_checker.check_code(student_code, notebook_filename, task_id, time_limit, memory_limit)

    # Обработка результата
    if result['time'] is None or result['memory'] is None:
        return {'status': 'error', 'text': result['text']}

    # Создание решения
    solution = Solution.objects.create(
        user_id=user_id,
        task_id=task_id_,
        user_code=student_code,
        timestamp=timezone.now(),
        time=10,
        memory=10,
        score=0,
        # time=float(result['time'].split('#')[0]),
        # memory=float(result['memory'].split('#')[0]),
        # score=np.sqrt(float(result['time'].split('#')[0]) ** 2 + float(result['memory'].split('#')[0]) ** 2)
    )

    return {'status': 'success', 'solution_id': solution.id}