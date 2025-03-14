import time
import tracemalloc
from dataclasses import dataclass


tests = [
    (1, 3),
    (2, 4),
]

units = [
    'KiB',
    'MiB',
    'GiB',
    'TiB'
]


@dataclass
class Result:
    is_success: bool            # Выполнены ли все тесты
    error_test_id: int = 0      # На каком тесте произошла ошибка
    time: float = 0.0           # Затраченное время
    memory_peak: float = 0.0    # Максимальное количество выделенной памяти
    info: list = None           # В случае ошибки имеет вид: [необходимое значение, полученное]


def create_py_file(code: str):
    with open("course/files/student_code.py", "w", encoding="utf-8") as f:
        f.write(code)


def get_pretty_memory(memory: float):
    unit = 0
    while memory > 1024:
        unit += 1
        memory /= 1024
    return f'{memory:.2f} {units[unit]}'


def start_tests(fun, qa_tests):
    start_time = time.perf_counter()

    max_memory_usage = 0

    for test_idx, qa_test in enumerate(qa_tests, start=1):
        question, answer = qa_test

        tracemalloc.start()
        fun_answer = fun(question)

        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        max_memory_usage = max(peak / 1024, max_memory_usage)

        if fun_answer != answer:
            # Описывать ли ошибку?
            print(f'Ошибка в тесте номер {test_idx}\n\tЗначение функции: {fun_answer}\n\tТребуется: {answer}')
            return Result(
                is_success=False,
                error_test_id=test_idx,
                info=[answer, fun_answer]
            )

    end_time = time.perf_counter()

    print(f'Всё верно.\n\tВремя: {end_time - start_time:.6f}\n\tМаксимум загрузки памяти: {get_pretty_memory(max_memory_usage)}')

    return Result(
        is_success=True,
        time=round(end_time - start_time, 6),
        memory_peak=max_memory_usage
    )


def check_code(code: str):
    # Создаём файл
    create_py_file(code)

    # Открываем файл
    try:
        from course.files.student_code import my_fun

        # Запускаем тесты
        start_tests(my_fun, tests)

    except Exception as e:
        print("Ошибка при выполнении кода:", e)
