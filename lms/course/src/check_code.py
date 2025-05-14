import time
import nbformat
from nbformat.notebooknode import NotebookNode
from jupyterhub.services.auth import HubAuth
import re
import requests
from websocket import create_connection, WebSocketTimeoutException
import json
import uuid

# from config import Config
# from logging_config import logger

from course.src.config import Config
from course.src.logging_config import logger

settings = Config.from_yaml("config.yaml")

# todo Добавить обработку различный единиц измерения времени 1
# todo Добавить обработку различный единиц измерения памяти 2
# todo Добавить celery           7


class NotebookChecker:
    def __init__(self):
        self.JUPYTERHUB_URL = "http://jupyterhub:8000/hub/api"
        self.API_TOKEN = "07551b6a34fa4bbbac6fe6d3645fc6d8"
        self.BASE_URL = "http://jupyterhub:8000/user/user1/api"
        self.USERNAME = "user1"
        self.server_is_running = False
        self.kernel_id = None
        self.timeout = 100  # ms

        self.start_jupyter_server()
        logger.info('ЗДЕСЬ')

        self.session = requests.Session()
        self.ws = self.get_ws_connection()

    def start_jupyter_server(self):
        headers = {
            "Authorization": f"token {self.API_TOKEN}"
        }
        resp = requests.post(f"{self.JUPYTERHUB_URL}/users/{self.USERNAME}/server", headers=headers)

        if resp.status_code == 201:
            logger.info("Сервер запущен.")  #
        elif resp.status_code == 202:
            logger.info("Сервер уже запускается.") #
            while resp.status_code == 202:
                logger.info('ЖДУ ЗАПУСКА')
                time.sleep(10)
                resp = requests.post(f"{self.JUPYTERHUB_URL}/users/{self.USERNAME}/server", headers=headers)

        elif resp.status_code == 400:
            logger.info("Сервер уже запущен.") #
        else:
            logger.error(f"Ошибка: {resp.status_code}, {resp.text}")

    def create_kernel(self):
        server_url = f"http://jupyterhub:8000/user/{self.USERNAME}/api"
        user_headers = {
            "Authorization": f"token {self.API_TOKEN}"
        }

        # Создаём новое ядро
        resp = requests.post(f"{server_url}/kernels", headers=user_headers)
        kernel = resp.json()
        logger.info('Ядро создано') #
        self.kernel_id = kernel["id"]

    def kill_kernel(self):
        # todo: Объединить переменные 3
        JUPYTERHUB_URL = "http://jupyterhub:8000"

        # Базовый путь к API ядра данного пользователя
        base_api = f"{JUPYTERHUB_URL}/user/{self.USERNAME}/api"

        self.session.headers.update({"Authorization": f"token {self.API_TOKEN}"})

        resp = self.session.get(f"{base_api}/kernels")
        resp.raise_for_status()
        xsrf = self.session.cookies.get("_xsrf")

        delete_resp = self.session.delete(
            f"{base_api}/kernels/{self.kernel_id}",
            headers={"X-XSRFToken": xsrf}
        )

        if delete_resp.status_code == 204:
            logger.info(f"Ядро {self.kernel_id} успешно остановлено/удалено.") #
        else:
            logger.error(f"Не удалось удалить ядро: {delete_resp.status_code}")
            logger.error(delete_resp.text)

    def get_ws_connection(self):

        self.session.headers.update({"Authorization": f"token {self.API_TOKEN}"})

        base_api = f"http://jupyterhub:8000/user/{self.USERNAME}/api"
        resp = self.session.get(f"{base_api}/kernels")
        resp.raise_for_status()

        # todo  меняется ли он 4
        xsrf = self.session.cookies.get("_xsrf")

        self.create_kernel()

        ws_url = f"ws://jupyterhub:8000/user/{self.USERNAME}/api/kernels/{self.kernel_id}/channels"

        return create_connection(
            ws_url,
            header=[
                f"Authorization: token {self.API_TOKEN}",
                f"X-XSRFToken: {xsrf}"
            ],
            cookie=f"_xsrf={xsrf}"
        )

    def check_code(self, student_code, filename, task_id, time_limit, memory_limit):
        """
            Функция для проверки кода ученика

            @param student_code: str - Код ученика
            @param filename: str - Файл с тестами
            @param task_id:
            @param time_limit:
            @param memory_limit:
            @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
            'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
            'text' будет описана ошибка, а остальные поля будут иметь None
            """

        logger.info('code: %s', student_code)
        logger.info('filename: %s', filename)
        logger.info('task_id: %s', task_id)
        # logger.info('code: %s', student_code)

        new_notebook, cell_with_code_idx = self.insert_code(filename, student_code, task_id, save_templates=True)
        result = self.check_notebook(new_notebook, task_id, cell_with_code_idx, time_limit, memory_limit)
        self.kill_kernel()
        return result

    def insert_code(self, file_name: str, user_code: str, task_id: str, save_templates=False) -> (NotebookNode, int):
        """
        Функция для добавления кода учения в file_name с тестами

        @param file_name: str       - Файл, в котором прописаны тесты
        @param user_code: str       - Код ученика
        @param task_id: str
        @param save_templates: bool - Если True, то после обработки файла file_name итоговый файл сохранится
        @return: NotebookNode       - Итоговый файл с кодом ученика и тестами

        """
        with open(file_name, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        # nb['cells'].insert(0, nbformat.v4.new_code_cell("%load_ext memory_profiler"))

        cell_idx = None

        for cell_idx in range(len(nb['cells'])):
            if nb['cells'][cell_idx]['id'] == task_id:
                break
        cell_idx += 1
        # todo: а если такой ячейки нет 5

        nb['cells'][cell_idx]['source'] = user_code

        # добавление функционала в ячейку с тестами
        # self.notebook_preproc(nb, cell_idx)

        if save_templates:
            with open(settings.template_file, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)

        return nb, cell_idx

    @staticmethod
    def notebook_preproc(notebook: NotebookNode, cell_with_code) -> None:
        """
        Предобработка тестов, прописанных в notebook
        Функция добавляет возможность расчёта максимальной нагрузки на память при тестировании
        путём добавления строк в начало и в конец ячейки с тестами.

        @param notebook: Загруженный файл .ipynd
        @param cell_with_code:
        """
        start_memory_time_check = '%%time\n%%memit\n'
        e = notebook.cells[cell_with_code + 1].source
        notebook.cells[cell_with_code + 1].source = start_memory_time_check + notebook.cells[cell_with_code + 1].source

    @staticmethod
    def get_restrictions(notebook: NotebookNode) -> (float, float):
        """
        Функция для чтения параметров из третьей ячейки

        @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
        @return: (float, float) - timeout, max_memory
        """

        if len(notebook.cells) < 3:
            # Параметры не заданы => ограничений нет
            logger.info('TimeLimit: inf\nMemoryLimit: inf') #
            return float('inf'), float('inf')

        cell_text = notebook.cells[2]['source']

        timeout = re.search(r'timeout\s*=\s*([0-9\.]*)', cell_text)[1]
        memory_max = re.search(r'memory_max\s*=\s*([0-9\.]*)', cell_text)[1]

        logger.info(f'TimeLimit: {timeout}\nMemoryLimit: {memory_max}') #
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
            logger.info('Ядро перезагружено')  #

    def send_code_and_wait(self, code: str):
        # todo Разобраться 6
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
            logger.info(f'wait results: {end_time - start_time} / {self.timeout}')  #
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

    @staticmethod
    def get_info(result):
        text = ''
        memory = 0
        time_ = 0

        pattern_memory = r'peak memory: ([0-9\.]+) .*? increment: ([0-9\.]+)'
        pattern_time = r'CPU times: .*? total: ([0-9\.]+)'

        for line in result.split('\n'):
            if line.startwith('peak memory'):
                memory = re.findall(pattern_memory, line)[0][1]
            elif line.startwith('CPU times:'):
                time_ = re.findall(pattern_time, line)[0]
            else:
                text += line + '\n'

        return text, time_, memory

    def check_notebook(self, notebook: NotebookNode, task_id, cell_with_code_idx, time_limit, memory_limit) -> dict:
        """
        Функция для выполнения ноутбука

        @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
        @param task_id:
        @param cell_with_code_idx:
        @param time_limit:
        @param memory_limit:
        @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
        'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
        'text' будет описана ошибка, а остальные поля будут иметь None
        """

        # Служебные функции
        # self.send_code_and_wait(notebook['cells'][0]['source'])

        # Выполнение ноутбука
        try:
            code = notebook['cells'][cell_with_code_idx]['source']
            self.send_code_and_wait(code)

            tests = notebook['cells'][cell_with_code_idx + 1]['source']
            result = self.send_code_and_wait(tests)
            logger.info(result)

            # text, time_, memory = self.get_info(result)

            return {
                'text': result,
                'time': 10,
                'memory': 10,
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
            """,
            'LMS.ipynb',
            task_id='095f1c66-fec2-4f9e-a487-5a1e75e4b505',
            time_limit=10,
            memory_limit=100
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