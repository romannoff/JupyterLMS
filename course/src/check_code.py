import time
import nbformat
from nbformat.notebooknode import NotebookNode
import re
import requests
from websocket import create_connection, WebSocketTimeoutException
import json
import uuid

from src.config import Config
from src.logging_config import logger

settings = Config.from_yaml("config.yaml")

class NotebookChecker:
    def __init__(self):
        self.JUPYTERHUB_URL = "http://localhost:8000/hub/api"
        self.API_TOKEN = "07551b6a34fa4bbbac6fe6d3645fc6d8"
        self.BASE_URL = "http://localhost:8000/user/user1/api"
        self.USERNAME = "user1"
        self.server_is_running = False
        self.kernel_id = None
        self.timeout = 100  # sec

        self.start_jupyter_server()

        self.session = requests.Session()
        self.ws = self.get_ws_connection()

    def start_jupyter_server(self):
        headers = {
            "Authorization": f"token {self.API_TOKEN}"
        }
        resp = requests.post(f"{self.JUPYTERHUB_URL}/users/{self.USERNAME}/server", headers=headers)

        if resp.status_code == 201:
            logger.debug("Сервер запущен.")
        elif resp.status_code == 202:
            logger.debug("Сервер уже запускается.")
        elif resp.status_code == 400:
            logger.debug("Сервер уже запущен.")
        else:
            logger.error(f"Ошибка: {resp.status_code}, {resp.text}")

    def get_ws_connection(self):

        self.session.headers.update({"Authorization": f"token {self.API_TOKEN}"})

        base_api = f"http://localhost:8000/user/{self.USERNAME}/api"
        resp = self.session.get(f"{base_api}/kernels")
        resp.raise_for_status()

        xsrf = self.session.cookies.get("_xsrf")
        self.kernel_id = resp.json()[0]["id"]

        ws_url = f"ws://localhost:8000/user/{self.USERNAME}/api/kernels/{self.kernel_id}/channels"

        return create_connection(
            ws_url,
            header=[
                f"Authorization: token {self.API_TOKEN}",
                f"X-XSRFToken: {xsrf}"
            ],
            cookie=f"_xsrf={xsrf}"
        )

    def check_code(self, student_code, filename=settings.file_name):
        """
            Функция для проверки кода ученика

            @param student_code: str - Код ученика
            @param filename: str - Файл с тестами
            @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
            'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
            'text' будет описана ошибка, а остальные поля будут иметь None
            """
        new_notebook = self.insert_code(filename, student_code, save_templates=True)
        return self.check_notebook(new_notebook)

    def insert_code(self, file_name: str, user_code: str, save_templates=False) -> NotebookNode:
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
        self.notebook_preproc(nb)

        if save_templates:
            with open(settings.template_file, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)

        return nb

    @staticmethod
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

    @staticmethod
    def get_restrictions(notebook: NotebookNode) -> (float, float):
        """
        Функция для чтения параметров из третьей ячейки

        @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
        @return: (float, float) - timeout, max_memory
        """

        if len(notebook.cells) < 3:
            # Параметры не заданы => ограничений нет
            logger.debug('TimeLimit: inf\nMemoryLimit: inf')
            return float('inf'), float('inf')

        cell_text = notebook.cells[2]['source']

        timeout = re.search(r'timeout\s*=\s*([0-9\.]*)', cell_text)[1]
        memory_max = re.search(r'memory_max\s*=\s*([0-9\.]*)', cell_text)[1]

        logger.debug(f'TimeLimit: {timeout}\nMemoryLimit: {memory_max}')
        return float(timeout), float(memory_max)

    @staticmethod
    def get_time(seconds_count: float) -> str:
        """
        Функция достаёт из результата выполнения ноутбука время выполнения тестов

        @param seconds_count: float - Время выполнения ячеек
        @return: str - Время выполнения кода (секунд)
        """
        return f'{seconds_count:.2f} sec.'

    @staticmethod
    def get_pretty_memory(memory):
        unit = 0
        while memory > 1024:
            unit += 1
            memory /= 1024
        return f'{memory:.2f} {settings.units[unit]}'

    def get_memory(self, notebook_output: str, max_memory: float) -> str:
        """
        Функция для получения пиковой нагрузки на память во время выполнения тестов

        @param notebook_output: str - Результат выполнения ячеек ноутбука
        @param max_memory: float - Ограничение по памяти
        @return: str - Пиковая нагрузка на память. Если пиковая нагрузка больше допустимой,
        то вернётся 'ERROR'
        """
        _, memory = notebook_output.split(settings.delimiter)
        memory = float(memory)
        memory_str = self.get_pretty_memory(memory)

        if memory > max_memory:
            raise MemoryError(f'MemoryError: \nCurrent memory: {memory_str}\nLimit: {max_memory}KiB')
        return memory_str

    def restart_kernel(self):
        if self.kernel_id is not None:
            resp = self.session.post(f"{self.BASE_URL}/kernels/{self.kernel_id}/restart")
            resp.raise_for_status()
            logger.debug('Ядро перезагружено')

    def send_code_and_wait(self, code: str):
        header = {
            "msg_id": uuid.uuid4().hex,
            "username": self.USERNAME,
            "session": uuid.uuid4().hex,
            "msg_type": "execute_request",
            "version": "5.3"
        }
        content = {
            "code": code,
            "silent": False,
            "store_history": False,
            "user_expressions": {},
            "allow_stdin": False
        }
        msg = {"header": header, "parent_header": {}, "metadata": {}, "content": content}
        self.ws.send(json.dumps(msg))
        self.ws.settimeout(1.0)

        result = ''

        start_time = time.time()

        while (end_time := time.time()) - start_time < self.timeout:
            logger.debug(f'wait results: {end_time - start_time} / {self.timeout}')
            try:
                raw = self.ws.recv()
            except WebSocketTimeoutException:
                continue

            m = json.loads(raw)

            # пропускаем чужие сообщения
            parent = m.get("parent_header", {})
            if parent.get("msg_id") != header["msg_id"]:
                continue

            # вывод потоков print()/stderr
            if m["msg_type"] == "stream":
                result += m["content"]["text"]

            # return значения
            elif m["msg_type"] == "execute_result":
                data = m["content"].get("data", {})
                if "text/plain" in data:
                    result += data["text/plain"] + '\n'

            # ошибки
            elif m["msg_type"] == "error":
                raise RuntimeError(f"{m['content']['ename']}: {m['content']['evalue']}")

            # собственно, конец исполнения
            elif m["msg_type"] == "status" and m["content"].get("execution_state") == "idle":
                return result, end_time - start_time
        # время выполнения превышено
        else:
            self.session.post(f"{self.BASE_URL}/kernels/{self.kernel_id}/interrupt")
            raise RuntimeError(f"TimeoutError:\n current time: {self.get_time(end_time - start_time)}\n limit: {self.timeout} sec")

    def check_notebook(self, notebook: NotebookNode) -> dict:
        """
        Функция для выполнения ноутбука

        @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
        @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
        'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
        'text' будет описана ошибка, а остальные поля будут иметь None
        """

        self.timeout, memory_max = self.get_restrictions(notebook)

        self.restart_kernel()

        # Выполнение ноутбука
        try:

            result = ''
            execute_time = 0

            for cell in notebook['cells'][:2]:
                code = cell['source']
                output_text, output_time = self.send_code_and_wait(code)

                result += output_text
                execute_time += output_time

            text = result.split('#%423#')[0]
            memory_peak = self.get_memory(result, memory_max)

            return {
                'text': text,
                'time': self.get_time(execute_time),
                'memory': memory_peak,
            }

        # В ячейке ошибка
        except RuntimeError as e:
            return {
                'text': e.args[0],
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

        except Exception as e:
            return {
                'text': e,
                'time': None,
                'memory': None,
            }


if __name__ == '__main__':
    e = NotebookChecker()
    print(
        e.check_code(
            """
            def my_fun(a, b):
                return a + b 
            """
        )
    )

"""
def my_fun(a, b):
    e = list(range(1000))
    return a + b
"""

"""
import time
def my_fun(a, b):
    time.sleep(10)
    return a + b
"""

"""
def my_fun(a, b):
    return a + b
"""