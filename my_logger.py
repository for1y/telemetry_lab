
import logging
import time
import threading

class CustomLogger:
    def __init__(self, name="log"):
        self.name = name
        self.log_file = open(f"{name}.txt", "w")
        self.lock = threading.Lock()

    def _write(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        with self.lock:
            self.log_file.write(formatted_message)
            self.log_file.flush()

    def debug(self, message):
        self._write(f"[DEBUG]: {message}")

    def info(self, message):
        self._write(f"[INFO]: {message}")

    def warning(self, message):
        self._write(f"[WARNING]: {message}")

    def error(self, message):
        self._write(f"[ERROR]: {message}")

    def critical(self, message):
        self._write(f"[CRITICAL]: {message}")

    def drone_moves(self, message):
        self._write(f"[DRONE MOVES]: {message}")
    def alarms_and_triggers(self, message):
        self._write(f"[ALARMS AND TRIGGERS]: {message}")
    def operator_actions(self, message):
        self._write(f"[OPERATOR ACTIONS]: {message}")
    def any_moves(self, message):
        self._write(f"[ANY]: {message}")



def get_logger():
    """
    Создаёт и возвращает настроенный логгер.
    :return: Логгер.
    """
    # Создаём логгер
    # logger = logging.getLogger(logger_name)
    logger_1 =CustomLogger()
    return logger_1

logger = get_logger()