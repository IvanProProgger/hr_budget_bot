from datetime import datetime

from config.config import Config
from db import db
from helper.message_manager import message_manager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def validate_period_dates(period: str) -> str:
    """
    Проверяет корректность формата дат в периоде.

    :param period: Строка с датами в формате dd.mm.yy
    :return: Строка с датами в формате dd.mm.yyyy, разделенными пробелом
    :raises RuntimeError: При некорректном формате дат
    """

    try:
        return " ".join(
            [
                datetime.strptime(f"01.{date}", "%d.%m.%y").strftime("%d.%m.%Y")
                for date in period.split()
            ]
        )
    except Exception as e:
        raise RuntimeError(
            f"Введены неверные даты. Даты вводятся в формате mm.yy. "
            f'строго через пробел(например: "08.22 10.22").\n'
            f"Ошибка: {e}"
        )


async def get_record_by_id(row_id: int) -> dict:
    """
    Получает запись из базы данных по id.

    :param row_id: ID записи для получения
    :return: Словарь с данными записи
    """

    async with db:
        record_dict = await db.get_row_by_id(row_id)

    return record_dict


async def get_record_info(record_dict: dict) -> str:
    """
    Получает детали конкретного счета из базы данных и форматирует их для бота.

    :param record_dict: Словарь с данными счета
    :return: Форматированная строка с информацией о счете
    """

    return (
        f"Данные счета:\n"
        f'1.Сумма: {record_dict["amount"]}₽;\n'
        f'2.Статья: "{record_dict["item"]}"\n'
        f'3.Группа: "{record_dict["groupment"]}"\n'
        f'4.Комментарий: "{record_dict["comment"]}"\n'
        f'5.Даты начисления: "{", ".join(record_dict["period"].split())}"\n'
        f'6.Форма оплаты: "{record_dict["payment_method"]}"\n'
    )


async def create_approval_keyboard(
        row_id: str | int, department: str
) -> InlineKeyboardMarkup:
    """
    Создание кнопок "Одобрить" и "Отклонить",
    создание и отправка сообщения для одобрения заявки.

    :param row_id: ID записи для одобрения
    :param department: Название департамента
    :return: Объект InlineKeyboardMarkup с кнопками
    """

    keyboard = [
        [
            InlineKeyboardButton(
                text="Одобрить",
                callback_data=f"approval_approve_{department}_{row_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Отклонить",
                callback_data=f"approval_reject_{department}_{row_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def create_payment_keyboard(row_id: int) -> InlineKeyboardMarkup:
    """
    Создание кнопки "Оплачено".

    :param row_id: ID записи для подтверждения оплаты
    :return: Объект InlineKeyboardMarkup с кнопкой
    """

    keyboard = [[InlineKeyboardButton("Оплачено", callback_data=f"payment_{row_id}")]]
    return InlineKeyboardMarkup(keyboard)


async def split_long_message(message: str) -> list:
    """
    Разбивает длинное сообщение на части по 4096 символов.

    :param message: Длинное сообщение для разделения
    :return: Список частей сообщения
    """

    # Проверяем, нужно ли разбивать сообщение
    if len(message) <= 4096:
        return [message]

    # Делим сообщение на части
    parts = []
    while len(message) > 0:
        # Брать первую часть длиной до 4096 символов
        split_point = message.rfind("\n\n", 0, 4096)
        if split_point == -1:  # Если нет переноса строки, берём 4096 символов
            split_point = 4096

        parts.append(message[:split_point])
        message = message[split_point:].lstrip(
            "\n"
        )  # Удаляем переноса строки из начала следующей части

    return parts


async def get_chat_id_by_payment_method(
        payment_method: str,
) -> list[str | int] | str | int:
    """
    Возвращает chat_id пользователей бота из группы payments(плательщиков)
    в зависимости от указанного метода оплаты счёта.

    :param payment_method: Метод оплаты ("нал", "крипта", "безнал", "карта")
    :return: Строковое представление chat_id или список chat_id
    :raises RuntimeError: При отсутствии сотрудника для данной операции
    """

    if payment_method in ("нал", "крипта"):
        chat_id = ["594336984"]
    elif payment_method == "безнал":
        chat_id = ["594336984"]
    elif payment_method == "карта":
        chat_id = ["594336984"]

    if not chat_id:
        raise RuntimeError("Не найден сотрудник для данной операции")

    return chat_id


async def add_data_to_message_manager(
        record_dict: dict, row_id, initiator_chat_id: str | int
):
    """
    Добавляет данные в экземпляр класса MessageManager.

    :param record_dict: Словарь с данными счета
    :param row_id: ID записи
    :param initiator_chat_id: ID чата инициатора
    :raises RuntimeError: При ошибке добавления данных
    """

    try:
        record_data_text = await get_record_info(record_dict)
        amount = record_dict.get("amount")
        initiator_nickname = await get_nickname("initiator", initiator_chat_id)
        await message_manager.update_data(
            row_id,
            {
                "initiator_chat_id": initiator_chat_id,
                "initiator_nickname": initiator_nickname,
                "record_data_text": record_data_text,
                "amount": amount,
            },
        )
    except Exception as e:
        raise RuntimeError(
            f"Ошибка при добавлении данных в экземпляр класса MessageManager: {e}"
        )


async def update_storage_data(row_id, **kwargs: int | str | None) -> dict:
    """
    Обновляет данные в базе данных 'approvals' по номеру ячейки.

    :param row_id: ID записи для обновления
    :param kwargs: Ключевые слова для параметров обновления
    :return: Словарь с обновленными данными
    """

    async with db:
        exist_approver = await db.get_value("approved_by", row_id)
        if exist_approver and kwargs.get("approved_by"):
            kwargs["approved_by"] = f"{exist_approver} и {kwargs['approved_by']}"
        update_data = {key: value for key, value in kwargs.items() if value is not None}
        await db.update_row_by_id(row_id, update_data)
        record_dict = await db.get_row_by_id(row_id)

    if kwargs.get("approved_by"):
        await message_manager.update_data(
            row_id, {"approver": kwargs.get("approved_by")}
        )

    return record_dict


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
