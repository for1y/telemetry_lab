import random
import asyncio
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
import threading
import time
import psycopg2 as pg
import requests
from typing import List, Tuple

"""GLOBAL VARIABLES"""
host = '192.168.2.134'
dbname = 'student_practicals'
port = '5432'
username = 'student_7'
password = 'password7'
host_quad = '192.168.2.143'
port_quad = '5007'



class CopterController(QObject):
    cords = []
    def __init__(self, update_interval=1000):
        self.update_interval = update_interval
        # Координаты
        self.cords = self._get_cords()
        #
        self.running = True
        # Поток, связанный с этим объектом
        self.update_thread = threading.Thread(target=self.update_copter_cords)
        self.update_thread.start()
        #
        self.api_url = f"http://{host_quad}:{port_quad}"

    def update_copter_cords(self):
        while self.running:
            cords = data_from_database('realtime_telemetry', 1)[0][2:5]
            print(f'drone move to {cords}')
            self.cords = cords
            time.sleep(2)

    def set_target_position(self, cords: List[float]) -> None:
        payload = {'target_position': cords}

        # response = requests.post(f"{self.api_url}/target_position", json=payload)
        response_imitation = True
        # if response.status_code == 200:
        if response_imitation:
            print(f'[SUCCESS] set_target_position {cords}')
        else:
            print(f'[FAILURE] set_target_position {cords}')

    def block_swiching(self, block: bool):
        payload = {"block": block}
        response = requests.post(f"{self.api_url}/block_switching", json=payload)
        if response.status_code == 200:
            print(f'[SUCCESS] block_swiching {block}')
        else:
            print(f'[FAILURE] block_swiching {block}')

    def get_copter_telemetry(self, count_of_records):
        data = data_from_database('realtime_telemetry', count_of_records)
        return data

    def _get_cords(self):
        data = data_from_database('realtime_telemetry', 1)
        return data[0][2:5]

    def show_telemetry(self, count_of_records=1):
        data = self.get_copter_telemetry(count_of_records)
        data.append(tuple(['id', 'time', 'x', 'y', 'z', 'x', 'y', 'z']))
        data.reverse()
        self.print_data(data)

    def print_data(self, data: List[Tuple]):
        if not data or not isinstance(data[0], tuple):  # Проверка на пустой список или неправильный формат
            print("Неверный формат данных!")
            return

        # Определим количество столбцов и максимальную ширину каждого из них
        num_columns = len(data[0])
        column_widths = [max(len(str(row[i])) for row in data) for i in range(num_columns)]

        # Форматирование строки
        format_string = "  ".join(f'{{:<{width}}}' for width in column_widths)

        # Печать заголовка таблицы
        print(format_string.format(*data[0]))
        print("-" * (sum(column_widths) + (num_columns - 1) * 2))  # Разделитель

        # Печать строк таблицы
        for row in data[1:]:
            print(format_string.format(*row))


def data_from_database(table_name, count_of_records=50):
    # with pg.connect(
    #         dbname=dbname,
    #         user=username,
    #         password=password,
    #         host=host,
    #         port=port) as connect:
    #     cursor = connect.cursor()
    #     cursor.execute(f"""SELECT * FROM {table_name} ORDER BY id DESC LIMIT {count_of_records}""")
    #     data = cursor.fetchall()

    # имитация данных
    data = [
        [
            random.randint(1, 10),
            _,
            random.randint(-25000, 25000) / 1000.0,
            random.randint(-25000, 25000) / 1000.0,
            random.randint(-25000, 25000) / 1000.0,
            random.randint(-25000, 25000) / 1000.0,
            random.randint(-25000, 25000) / 1000.0,
            random.randint(-25000, 25000) / 1000.0
        ]
        for _ in range(count_of_records)  # Обратить внимание на range()
    ]
    return data

# Инициализация глобальной переменной коптера
