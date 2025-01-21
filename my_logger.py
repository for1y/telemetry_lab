import logging


def get_logger(log_file="logs.txt", logger_name="AppLogger", level=logging.DEBUG):
    """
    Создаёт и возвращает настроенный логгер.

    :param log_file: Путь к файлу, куда будут записываться логи.
    :param logger_name: Имя логгера.
    :param level: Уровень логирования (по умолчанию INFO).
    :return: Логгер.
    """
    # Создаём логгер
    logger = logging.getLogger(logger_name)

    # Проверяем, добавлены ли уже обработчики
    if not logger.hasHandlers():
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

        # Добавляем обработчик к логгеру
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger

logger = get_logger()