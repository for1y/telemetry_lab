import threading
import time
import random


class CopterController:
    def __init__(self, update_interval=3):
        self.update_interval = update_interval
        self.cords = [0.0, 0.0, 0.0]
        self.running = True
        # Поток, связанный с этим объектом
        self.update_thread = threading.Thread(target=self.update_coordinates)
        self.update_thread.start()

    def update_coordinates(self):
        """Обновление координат в фоновом режиме."""
        while self.running:
            # Генерация случайных координат
            self.cords = [
                random.uniform(-250.0, 250.0),
                random.uniform(-250.0, 250.0),
                random.uniform(-250.0, 250.0),
            ]
            print(f"Updated coordinates {self.update_interval}: {self.cords}")
            time.sleep(self.update_interval)

    def stop(self):
        """Остановить поток обновления."""
        self.running = False
        self.update_thread.join()

    def get_current_coordinates(self):
        return self.cords


# Пример использования
controller1 = CopterController(update_interval=2)
controller2 = CopterController(update_interval=5)

try:
    time.sleep(10)  # Имитация работы программы
finally:
    controller1.stop()
    controller2.stop()