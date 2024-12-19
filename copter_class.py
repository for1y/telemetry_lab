import random

from PyQt5.QtCore import QThread, pyqtSignal, QObject

import psycopg2 as pg
import requests
from typing import List, Tuple

from PyQt5.QtCore import QTimer

"""GLOBAL VARIABLES"""
host = '192.168.2.134'
dbname = 'student_practicals'
port = '5432'
username = 'student_7'
password = 'password7'
host_quad = '192.168.2.143'
port_quad = '5007'


class CoordinateUpdater(QThread):
    coordinates_updated = pyqtSignal(list)  # Сигнал для передачи обновленных координат

    def __init__(self, copter_controller):
        super().__init__()
        self.copter_controller = copter_controller
        self.running = True  # Флаг для управления потоком

    def run(self):
        while self.running:
            coords = self.copter_controller._get_cords()  # Получение новых координат
            self.coordinates_updated.emit(coords)  # Генерация сигнала
            self.msleep(1000)  # Интервал обновления 1 секунда

    def stop(self):
        self.running = False
        self.wait()  # Ожидаем завершения потока


class CopterController(QObject):
    def __init__(self):
        # Координаты
        self.cords = [0.0, 0.0, 0.0]
        self.updater = CoordinateUpdater(self)  # Создаем экземпляр обновляющего потока
        self.updater.coordinates_updated.connect(self._update_coords)
        self.updater.start()  # Запускаем поток
        #
        self.api_url = f"http://{host_quad}:{port_quad}"

        # Таймер для обновления координат каждую секунду

    def _update_coords(self, cords):
        """Слот для получения обновленных координат от потока."""
        self.cords = cords
        self.coordinates_updated.emit(self.cords)  # Извещаем внешние компоненты

    def stop_updater(self):
        """Остановка потока."""
        self.updater.stop()

    def set_target_position(self, cords: List[float]) -> None:
        payload = {'target_position': cords}
        response = requests.post(f"{self.api_url}/target_position", json=payload)
        if response.status_code == 200:
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
        data = self.data_from_database('realtime_telemetry', count_of_records)
        return data

    def _get_cords(self):
        data = self.data_from_database('realtime_telemetry', 1)
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

    def data_from_database(self, table_name, count_of_records=50):
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


# # Инициализация глобальной переменной коптера
# global copter
# copter = CopterController()
