import nbformat
from nbformat.notebooknode import NotebookNode
from typing import TypedDict, List
import re


class Task(TypedDict):
    task_id: int            # Номер задания в курсе
    task_name: str          # Имя задания
    task_description: str   # Описание задания
    open_tests: str         # Открытые тесты
    backbone: str           # Запись в поле для ввода
    time_limit: float       # Ограничение по времени в секундах
    memory_limit: float     # Ограничение по памяти в Кбайтах


class Course(TypedDict):
    course_id: str          # Путь до ноутбука
    course_name: str        # Имя курса
    tasks: List[Task]       # Список задач в курсе


def get_no_hidden_text(cell):
    text = []
    lines = cell.split('\n')

    is_hidden = False

    for line in lines:
        if line.strip() == '#HIDDEN':
            is_hidden = bool((is_hidden + 1) % 2)
        elif not is_hidden:
            text.append(line)
    return '\n'.join(text)


def get_restrictions(text) -> (float, float):
    timeout = re.search(r'timeout\s*=\s*([0-9\.]*)', text)[1]
    memory_max = re.search(r'memory_max\s*=\s*([0-9\.]*)', text)[1]

    return float(timeout), float(memory_max)


def jupyter_parser(notebook_path):

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    if nb['cells'][0]['cell_type'] != 'markdown':
        RuntimeError(f'Первая ячейка {notebook_path} не markdown')

    course_name = re.sub('#', '', nb['cells'][0]['source']).strip()

    result = Course(
        course_name=course_name,
        course_id=notebook_path,
        tasks=[]
    )

    current_task = None
    counter = 3

    for cell in nb['cells'][1:]:
        if cell['cell_type'] == 'markdown':
            if counter < 2 and current_task is not None:
                RuntimeError(f'В задаче {current_task["task_name"]} обнаружено ячеек типа code: {counter}. '
                             f'Необходимо как минимум две - начальный код и тесты')

            if current_task is not None:
                result['tasks'].append(current_task)

            task_name, task_description = cell['source'].split('\n')

            task_name = re.sub('#', '', task_name).strip()

            current_task = Task(
                task_id=cell['id'],
                task_name=task_name,
                task_description=task_description,
                open_tests='',
                backbone='',
                time_limit=float('inf'),
                memory_limit=float('inf'),
            )
            counter = 0
            continue

        text = get_no_hidden_text(cell['source'])

        if counter == 0:
            current_task['backbone'] = text

        elif counter == 1:
            current_task['open_tests'] = text

        elif counter == 2:
            current_task['time_limit'], current_task['memory_limit'] = get_restrictions(text)

        counter += 1

    if current_task is not None:
        result['tasks'].append(current_task)

    return result


if __name__ == '__main__':
    print(jupyter_parser('LMS2.ipynb'))
