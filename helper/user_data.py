from config.config import Config
from helper.logging_config import logger


async def get_nickname(department: str, chat_id: str | int) -> str:
    """
    Возвращает nickname для заданного департамента и chat_id.

    :param department: Название департамента
    :param chat_id: ID чата для получения nickname
    :return: Nickname для указанного chat_id в указанном департаменте
    """

    chat_ids = Config.NICKNAMES.get(department)
    if chat_ids:
        return chat_ids.get(str(chat_id), "")


async def get_department(chat_id: str | int) -> str:
    """
    Возвращает название департамента по заданному chat_id.

    :param chat_id: ID чата для определения департамента
    :return: Название департамента или None, если не найдено
    """

    return Config.DEPARTMENTS.get(str(chat_id)) or None


async def get_chat_ids(department: str) -> list[str]:
    """
    Возвращает список chat_id для указанного департамента.

    :param department: Название департамента
    :return: Список строковых представлений chat_id
    """

    return [
        str(chat_id) for chat_id in getattr(Config, f"{department.lower()}_chat_ids")
    ]


async def get_departments(chat_id: str) -> list[str] | None:
    """
    Возвращает список департаментов, связанных с заданным chat_id.

    :param chat_id: ID чата для определения департаментов
    :return: Список названий департаментов или None, если не найдено
    :raises ValueError: Если департамент не найден для заданного chat_id
    """

    try:
        departments = {}
        for department in ["initiator", "head", "finance", "payers"]:
            for chat_id in getattr(Config, f"{department}_chat_ids"):
                if chat_id not in departments:
                    departments[chat_id] = []
                departments[chat_id].append(department)

        user_department = departments.get(chat_id)
        if not user_department:
            raise ValueError(f"Департамент не найден для введённого chat_id: {chat_id}")

        return user_department
    except Exception as e:
        logger.error(f"Ошибка поиска департамента по {chat_id}. Ошибка: {str(e)}")
        return None


async def get_chat_id_by_nickname(nickname):
    """
    Возвращает chat_id по нику пользователя telegram.

    :param nickname: Имя пользователя для поиска
    :return: Строковое представление chat_id или None, если не найдено
    """

    for role, nick_dict in Config.NICKNAMES.items():
        for chat_number, nick in nick_dict.items():
            if nick == nickname:
                return chat_number
    return None
