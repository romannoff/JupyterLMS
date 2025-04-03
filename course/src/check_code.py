from jupyter_client import KernelManager
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, DeadKernelError, CellTimeoutError
from datetime import datetime
from course.src.config import Config
from nbformat.notebooknode import NotebookNode
import re

settings = Config.from_yaml("config.yaml")


def notebook_preproc(notebook: NotebookNode) -> None:
    """
    Предобработка тестов, прописанных в notebook
    Функция добавляет возможность расчёта максимальной нагрузки на память при тестировании
    путём добавления строк в начало и в конец ячейки с тестами.

    @param notebook: Загруженный файл .ipynd
    """
    start_memory_check = 'import tracemalloc \ntracemalloc.start()\n'
    end_memory_check = f'\n_, peak = tracemalloc.get_traced_memory()\ntracemalloc.stop()\nprint("{settings.delimiter}", peak / 1024)'

    notebook.cells[1].source = start_memory_check + notebook.cells[1].source + end_memory_check


def get_restrictions(notebook: NotebookNode) -> (float, float):
    """
    Функция для чтения параметров из третьей ячейки

    @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
    @return: (float, float) - timeout, max_memory
    """

    if len(notebook.cells) < 3:
        # Параметры не заданы => ограничений нет
        return float('inf'), float('inf')

    cell_text = notebook.cells[2]['source']

    timeout = re.search(r'timeout\s*=\s*([0-9\.]*)', cell_text)[1]
    memory_max = re.search(r'memory_max\s*=\s*([0-9\.]*)', cell_text)[1]

    return float(timeout), float(memory_max)


def insert_code(file_name: str, user_code: str, save_templates=False) -> NotebookNode:
    """
    Функция дл добавления кода учения в file_name с тестами

    @param file_name: str       - Файл, в котором прописаны тесты
    @param user_code: str       - Код ученика
    @param save_templates: bool - Если True, то после обработки файла file_name итоговый файл сохранится
    @return: NotebookNode       - Итоговый файл с кодом ученика и тестами

    """
    with open(file_name, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    # Проверяем файл на пустоту
    assert len(nb.cells) >= 2, f'Файл {file_name} имеет некорректное количество ячеек'

    # Вставляем код ученика
    nb.cells[0].source = user_code

    # добавление функционала в ячейку с тестами
    notebook_preproc(nb)

    if save_templates:
        with open(settings.template_file, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)

    return nb


def get_time(notebook_output: dict) -> str:
    """
    Функция достаёт из результата выполнения ноутбука время выполнения тестов

    @param notebook_output: dict - Результат выполнения ячеек ноутбука
    @return: str - Время выполнения кода (секунд)
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"

    start = datetime.strptime(notebook_output['cells'][1]['metadata']['execution']['iopub.status.busy'], fmt)
    end = datetime.strptime(notebook_output['cells'][1]['metadata']['execution']['iopub.status.idle'], fmt)

    delta = end - start
    return f'{delta.seconds}.{delta.microseconds} sec.'


def get_memory(notebook_output: dict, max_memory: float) -> str:
    """
    Функция для получения пиковой нагрузки на память во время выполнения тестов

    @param notebook_output: dict - Результат выполнения ячеек ноутбука
    @param max_memory: float - Ограничение по памяти
    @return: str - Пиковая нагрузка на память. Если пиковая нагрузка больше допустимой,
    то вернётся 'ERROR'
    """
    notebook_output_text = notebook_output['cells'][1]['outputs'][0]['text']
    _, memory = notebook_output_text.split(settings.delimiter)
    memory = float(memory)

    if memory > max_memory:
        raise MemoryError(f'Превышен порог {max_memory}KiB')

    # Выбор единиц измерения для памяти
    unit = 0
    while memory > 1024:
        unit += 1
        memory /= 1024
    return f'{memory:.2f} {settings.units[unit]}'


def check_notebook(notebook: NotebookNode) -> dict:
    """
    Функция для выполнения ноутбука

    @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
    @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
    'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
    'text' будет описана ошибка, а остальные поля будут иметь None
    """

    timeout, memory_max = get_restrictions(notebook)

    # Создаем клиент Jupyter, который будет выполнять код
    client = NotebookClient(
        notebook,
        kernel_name=settings.kernel_name,
        km=KernelManager(kernel_name=settings.kernel_name),
        kernel_url=settings.kernel_url,
        timeout=int(timeout),
    )

    # Выполнение ноутбука
    try:
        executed_nb = client.execute()

        text = executed_nb['cells'][1]['outputs'][0]['text'].split('#%423#')[0]
        memory_peak = get_memory(executed_nb, memory_max)
        execute_time = get_time(executed_nb)

        return {
            'text': text,
            'time': execute_time,
            'memory': memory_peak,
        }

    # В ячейке ошибка
    except CellExecutionError as e:
        return {
            'text': e.evalue,
            'time': None,
            'memory': None,
        }

    # Превышение порога памяти
    except MemoryError as e:
        return {
            'text': e,
            'time': None,
            'memory': None,
        }

    # Ячейка вылетела
    except DeadKernelError as e:
        return {
            'text': e,
            'time': None,
            'memory': None,
        }

    # Время выполнения истекло
    except CellTimeoutError:
        return {
            'text': f'A cell timed out while it was being executed, after 10 seconds.',
            'time': None,
            'memory': None,
        }


def check_code(student_code: str, filename=settings.file_name) -> dict:
    """
    Функция для проверки кода ученика

    @param student_code: str - Код ученика
    @param filename: str - Файл с тестами
    @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
    'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
    'text' будет описана ошибка, а остальные поля будут иметь None
    """
    new_notebook = insert_code(filename, student_code)
    return check_notebook(new_notebook)
