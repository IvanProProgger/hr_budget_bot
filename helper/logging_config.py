import logging

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def configure_logging():
    """Функция для настройки логирования проекта"""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.getLevelName(LOG_LEVEL))
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Логгер для вашего проекта
    logger = logging.getLogger("budget_automation_bot")
    logger.setLevel(logging.getLevelName(LOG_LEVEL))

    # Добавляем обработчик только к логгеру "budget_automation_bot"
    logger.addHandler(console_handler)

    return logger


logger = configure_logging()
