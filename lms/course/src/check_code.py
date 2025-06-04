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


class NotebookChecker:
    def __init__(self):
        self.DOMAIN = "jupyterhub:8000"
        self.JUPYTERHUB_URL = f"http://{self.DOMAIN}"
        self.API_TOKEN = "07551b6a34fa4bbbac6fe6d3645fc6d8"
        self.USERNAME = "user1"
        self.kernel_id = None

        self.start_jupyter_server()

        self.session = requests.Session()
        self.ws = self.get_ws_connection()

    def start_jupyter_server(self):
        headers = {
            "Authorization": f"token {self.API_TOKEN}"
        }
        resp = requests.post(f"{self.JUPYTERHUB_URL}/hub/api/users/{self.USERNAME}/server", headers=headers)

        if resp.status_code == 201:
            logger.info("Сервер запущен.")  #
        elif resp.status_code == 202:
            logger.info("Сервер уже запускается.")  #
            while resp.status_code == 202:
                logger.info('ЖДУ ЗАПУСКА')
                time.sleep(10)
                resp = requests.post(f"{self.JUPYTERHUB_URL}/hub/api/users/{self.USERNAME}/server", headers=headers)

        elif resp.status_code == 400:
            logger.info("Сервер уже запущен.") #
        else:
            logger.error(f"Ошибка: {resp.status_code}, {resp.text}")

    def create_kernel(self):
        server_url = f"{self.JUPYTERHUB_URL}/user/{self.USERNAME}/api"
        user_headers = {
            "Authorization": f"token {self.API_TOKEN}"
        }

        # Создаём новое ядро
        resp = requests.post(f"{server_url}/kernels", headers=user_headers)
        kernel = resp.json()
        logger.info('Ядро создано') #
        self.kernel_id = kernel["id"]

    def kill_kernel(self):

        # Базовый путь к API ядра данного пользователя
        base_api = f"{self.JUPYTERHUB_URL}/user/{self.USERNAME}/api"

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

        base_api = f"{self.JUPYTERHUB_URL}/user/{self.USERNAME}/api"
        resp = self.session.get(f"{base_api}/kernels")
        resp.raise_for_status()

        xsrf = self.session.cookies.get("_xsrf")

        self.create_kernel()

        ws_url = f"ws://{self.DOMAIN}/user/{self.USERNAME}/api/kernels/{self.kernel_id}/channels"

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
            @param filename: str - Файл с заданиями и тестами
            @param task_id: str - id jupyter ячейки, с которой начинается задание (хранится в базе даннх)
            @param time_limit: float - Ограничение в секундах
            @param memory_limit: float - Ограничение в MB
            @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
            'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
            'text' будет описана ошибка, а остальные поля будут иметь None
            """

        logger.info('code: %s', student_code)
        logger.info('filename: %s', filename)
        logger.info('task_id: %s', task_id)
        # logger.info('code: %s', student_code)

        # Добавляем функционал для трекинга затрат памяти и времени
        new_notebook, cell_with_code_idx = self.insert_code(filename, student_code, task_id, save_templates=False)

        # Проверка кода ученика
        result = self.check_notebook(new_notebook, cell_with_code_idx, time_limit, memory_limit)

        # Уничтожение созданного ядра
        self.kill_kernel()
        return result

    def insert_code(self, file_name: str, user_code: str, task_id: str, save_templates=False) -> (NotebookNode, int):
        """
        Функция для добавления кода учения в file_name с тестами

        @param file_name: str       - Файл, в котором прописаны тесты
        @param user_code: str       - Код ученика
        @param task_id: str         - id ячейки, с которой начинается задача
        @param save_templates: bool - Если True, то после обработки файла file_name итоговый файл сохранится
        @return: NotebookNode       - Итоговый файл с кодом ученика и тестами

        """
        # Загружаем ноутбук с заданиями и тестами
        with open(file_name, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        # В начало ноутбука добавляем импортирование библиотеки для трекинга памяти
        nb['cells'].insert(0, nbformat.v4.new_code_cell("import memory_profiler\n%load_ext memory_profiler"))

        # По task_id находим индекс ячейки, с которой начинается код ученика
        cell_idx = None

        for cell_idx in range(len(nb['cells'])):
            if nb['cells'][cell_idx]['id'] == task_id:
                break
        cell_idx += 1

        if cell_idx >= len(nb['cells']):
            raise RuntimeError(f"Не удалось найти ячейки с заданием. Необходима ячейка с id: {task_id}")

        # Вставляем код ученика в ячейку
        nb['cells'][cell_idx]['source'] = user_code

        # добавление функционала в ячейку с тестами
        self.notebook_preproc(nb, cell_idx)

        if save_templates:
            with open(settings.template_file, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)

        return nb, cell_idx

    @staticmethod
    def notebook_preproc(notebook: NotebookNode, cell_with_code) -> None:
        """
        Предобработка тестов, прописанных в notebook
        Функция добавляет возможность расчёта максимальной нагрузки на память при тестировании
        путём добавления строк в начало и в конец ячейки с тестами. Также добавляется возможность замера времени

        @param notebook: Загруженный файл .ipynd
        @param cell_with_code: int - индекс ячейки с кодом
        """

        start_memory_time_check = '%%time\n%%memit\n'
        notebook.cells[cell_with_code + 1].source = start_memory_time_check + notebook.cells[cell_with_code + 1].source

    def restart_kernel(self):
        if self.kernel_id is not None:
            resp = self.session.post(f"{self.JUPYTERHUB_URL}//user/user1/api/kernels/{self.kernel_id}/restart")
            resp.raise_for_status()
            logger.info('Ядро перезагружено')  #

    def send_code_and_wait(self, code: str, timeout: float = 10):
        header = {
            "msg_id": uuid.uuid4().hex,
            "username": self.USERNAME,
            "session": uuid.uuid4().hex,
            "msg_type": "execute_request",
            "version": "5.3"
        }
        content = {
            "code": code,
        }
        msg = {"header": header, "parent_header": {}, "metadata": {}, "content": content}
        self.ws.send(json.dumps(msg))
        self.ws.settimeout(1.0)

        result = ''

        start_time = time.time()

        while (end_time := time.time()) - start_time < timeout:
            logger.info(f'wait results: {end_time - start_time} / {timeout}')  #
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

            # Конец исполнения
            elif m["msg_type"] == "status" and m["content"].get("execution_state") == "idle":
                return result
        # время выполнения превышено
        else:
            self.session.post(f"{self.JUPYTERHUB_URL}/user/user1/api/kernels/{self.kernel_id}/interrupt")
            raise RuntimeError(f"TimeoutError:\n current time: {end_time - start_time}\n limit: {timeout} sec")

    @staticmethod
    def parse_wall_time(text: str) -> float:
        """
        Извлекает из строки время Wall time и возвращает его в секундах.
        Поддерживаются форматы:
          - 123 ms
          - 1.13 s
          - 1min 10s
          - 2h 37min 15s
        """
        m = re.search(r"Wall time:\s*([0-9hms\. ]+)", text)
        if not m:
            raise ValueError("Wall time not found")
        t = m.group(1).strip()
        total = 0.0
        # часы
        h = re.search(r"(\d+)\s*h", t)
        if h:
            total += int(h.group(1)) * 3600
        # минуты
        mn = re.search(r"(\d+)\s*min", t)
        if mn:
            total += int(mn.group(1)) * 60
        # секунды (целые или с дробями)
        s = re.search(r"(\d+(\.\d+)?)\s*s(?!\w)|(\d+(\.\d+)?)\s*s$", t)
        if s:
            total += float(s.group(1))
        # миллисекунды
        ms = re.search(r"(\d+(\.\d+)?)\s*ms", t)
        if ms:
            total += float(ms.group(1)) / 1000.0
        return total

    @staticmethod
    def parse_memory_increment(text: str) -> float:
        """
        Извлекает из строки increment памяти и возвращает её в мегабайтах (MB).
        Поддерживаются единицы KiB, MiB, GiB.
        MiB принимаются за MB; GiB умножаются на 1024; KiB делятся на 1024.
        """
        m = re.search(r"increment:\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGTiB]+)", text)
        if not m:
            raise ValueError("Memory increment not found")
        val, unit = float(m.group(1)), m.group(2)
        unit = unit.upper()
        # привести к MiB
        if unit == "KIB":
            val = val / 1024
        elif unit == "GIB":
            val = val * 1024
        elif unit in ("MIB", "MB"):
            val = val
        else:
            raise ValueError(f"Unsupported memory unit: {unit}")
        return val

    def get_info(self, result):
        """
        Функция для получения вывода, памяти и времени из вывода ячейки
        @param result: Вывод ячейки
        @return: (str, float, float) - результат, время (секунды), память (MB)
        """
        text = ''
        memory = 0
        time_ = 0

        for line in result.split('\n'):
            if line.startswith('peak memory'):
                memory = self.parse_memory_increment(line)
            elif line.startswith('Wall time'):
                time_ = self.parse_wall_time(line)
            elif line.startswith('CPU times'):
                continue
            else:
                text += line + '\n'

        return text, time_, memory

    def check_notebook(self, notebook: NotebookNode, cell_with_code_idx, time_limit, memory_limit) -> dict:
        """
        Функция для выполнения ноутбука

        @param notebook: NotebookNode - Обработанный ноутбук, готовый для проверки
        @param cell_with_code_idx: int - номер ячейки, с которой начинается код ученика
        @param time_limit: float - Ограничение в секундах
        @param memory_limit: float - Ограничение в байтах
        @return: dict - Если тесты пройдены успешно, то будет возвращён словарь с полями
        'text', 'time', 'memory'. Если тесты не выполнены или вызвано исключение, то в поле
        'text' будет описана ошибка, а остальные поля будут иметь None
        """

        # Импортируем модули для трекинга памяти
        self.send_code_and_wait(notebook['cells'][0]['source'])

        if notebook['cells'][1]['cell_type'] == 'code':
            self.send_code_and_wait(notebook['cells'][1]['source'])

        # Выполнение ноутбука
        try:
            # Выполняем код ученика
            code = notebook['cells'][cell_with_code_idx]['source']
            self.send_code_and_wait(code)

            # Выполняем тесты
            tests = notebook['cells'][cell_with_code_idx + 1]['source']
            result = self.send_code_and_wait(tests, time_limit)
            logger.info(result)

            text, time_, memory = self.get_info(result)

            if time_ > time_limit:
                # Превышение времени
                text = f"TimeoutError:\nCurrent time: {time_} sec\nLimit: {time_limit} sec"
                time_, memory = None, None

            if memory > memory_limit:
                # Превышение памяти
                text = f"MemoryError:\nCurrent memory increment: {memory} MB\nLimit: {memory_limit} MB"
                time_, memory = None, None

            return {
                'text': text,
                'time': time_,
                'memory': memory,
            }

        # В ячейке ошибка
        except RuntimeError as e:
            return {
                'text': e.args[0],
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
            import time
            def my_fun(a, b):
                time.sleep(10)
                return a + b
            """,
            'pandas.ipynb',
            task_id='095f1c66-fec2-4f9e-a487-5a1e75e4b505',
            time_limit=2,
            memory_limit=1
        )
    )

"""
def my_fun(a, b):
    return a + b 
"""

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