from db import db
from helper.logging_config import logger
from helper.messages import INITIATOR, HEAD, FINANCE, PAYMENT
from telegram import InlineKeyboardMarkup
from telegram.ext import ContextTypes


class MessageManager:
    """Класс для хранения данных и отправки сообщений по отделам"""

    _instance = None

    def __new__(cls):
        """
        Создает и возвращает единственный экземпляр класса MessageManager.

        :return: Единственный экземпляр MessageManager
        """

        if cls._instance is None:
            cls._instance = super(MessageManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Инициализирует экземпляр MessageManager.

        Создает пустой словарь для хранения данных и устанавливает соединение с базой данных.
        """

        self._data = {}
        self.db = db
        self.messages = {
            "initiator": INITIATOR,
            "head": HEAD,
            "finance": FINANCE,
            "payment": PAYMENT,
        }

    def __getitem__(self, row_id):
        """
        Позволяет обращаться к данным как к словарю.

        :param row_id: ID записи для доступа к соответствующим данным
        :return: Словарь данных для указанного row_id или пустой словарь, если данные не найдены
        """

        return self._data.get(row_id, {})

    def __getattr__(self, name: str):
        """
        Позволяет обращаться к данным через атрибуты.

        :param name: Имя атрибута для доступа к данным
        :return: Значение атрибута или исключение, если атрибут приватный
        """

        if name.startswith("_"):
            raise AttributeError(f"Нельзя получить доступ к приватному атрибуту {name}")
        return self._data.get(
            name, AttributeError(f"Нет свойства {name} в {self.__class__.__name__}")
        )

    def __setitem__(self, row_id: int, value: dict):
        """
        Добавляет или обновляет значение по ID ячейки.

        :param row_id: ID ячейки для записи данных
        :param value: Словарь значений для записи
        :raises ValueError: Если значение не является словарем
        """

        if not isinstance(value, dict):
            raise ValueError("Значение должно быть словарем.")
        self._data[row_id] = value

    def __delitem__(self, row_id: int):
        """
        Удаляет элемент по ID ячейки.

        :param row_id: ID ячейки для удаления
        :raises KeyError: Если ID ячейки не найден
        """

        if row_id in self._data:
            del self._data[row_id]
        else:
            raise KeyError("ID ячейки не найден.")

    async def __call__(self, row_id: int) -> dict[str, int]:
        """
        Возвращает данные для указанного row_id.

        :param row_id: ID записи для получения данных
        :return: Словарь данных для указанного row_id
        """

        return {"row_id": row_id, **self._data.get(row_id, {})}

    async def update_data(self, row_id: int, data_dict: dict):
        """
        Обновляет данные ячейки по ID.

        :param row_id: ID ячейки для обновления
        :param data_dict: Словарь новых данных для обновления
        """

        self._data.setdefault(row_id, {}).update(data_dict)

    async def get_message(self, department, stage, **kwargs) -> str:
        """
        Возвращает сообщение в зависимости от отдела и этапа одобрения платежа.

        :param department: Департамент для получения сообщения
        :param stage: Этап одобрения для получения сообщения
        :param kwargs: Аргументы для форматирования сообщения
        :return: Форматированное сообщение
        :raises ValueError: Если указаны неправильный департамент или этап
        """

        if department not in self.messages:
            raise ValueError(f"Неправильный департамент: {department}")

        if stage not in self.messages[department]:
            raise ValueError(f"Неправильная стадия для {department}: {stage}")

        try:
            return self.messages[department][stage].format(**kwargs)
        except Exception as e:
            logger.error(f"Ошибка при форматировании сообщения: {e}")
            raise ValueError(f"Ошибка при форматировании сообщения: {e}")

    async def send_messages_with_tracking(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        row_id,
        department: str,
        chat_ids: list[int | str] | int | str,
        stage: str,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> None:
        """
        Отправка сообщения в выбранные телеграм-чаты с сохранением message_id и user_id.

        :param context: Контекст бота Telegram
        :param row_id: ID записи для получения данных
        :param department: Департамент для отправки сообщения
        :param chat_ids: Список ID чатов для отправки сообщения
        :param stage: Этап одобрения для получения сообщения
        :param reply_markup: Опциональный параметр для кнопок ответа
        :raises ValueError: При ошибке получения сообщения
        """

        try:
            message_text = await self.get_message(
                department, stage, **await self(row_id)
            )
        except Exception as e:
            raise ValueError(
                f"Не удалось получить сообщение для отдела: {department} и этапа: {stage}"
            )

        if isinstance(chat_ids, (int, str)):
            chat_ids = [chat_ids]

        message_ids = []
        actual_chat_ids = []
        for chat_id in chat_ids:
            try:
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{message_text}",
                    reply_markup=reply_markup,
                )
                message_ids.append(message.message_id)
                actual_chat_ids.append(chat_id)
            except Exception as e:
                logger.info(
                    f"🚨Ошибка при отправке сообщения в chat_id: {chat_id}. Ошибка: {e}"
                )
                pass

        self[row_id][f"{department}_messages"] = list(zip(actual_chat_ids, message_ids))

    async def resend_messages_with_tracking(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        row_id: int,
        department: str,
        stage: str,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> None:
        """
        Отправляет новое и удаляет старое сообщение.

        :param context: Контекст бота Telegram
        :param row_id: ID записи для обновления
        :param department: Департамент для отправки сообщения
        :param stage: Этап одобрения для получения сообщения
        :param reply_markup: Опциональный параметр для кнопок ответа
        :raises RuntimeError: Если по ключу department_messages нет данных
        """

        key = f"{department}_messages"
        if self[row_id].get(key) is None:
            raise RuntimeError(f"Ошибка! По ключу {department}_messages нет данных!")

        try:
            message_text = await self.get_message(
                department, stage, **await self(row_id)
            )
        except Exception as e:
            raise ValueError(
                f"Не удалось получить сообщение для отдела: {department} и этапа: {stage}"
            )

        actual_chat_ids = []
        message_ids = []
        for chat_id, message_id in self[row_id].get(key):
            try:
                message = await context.bot.send_message(
                    chat_id=chat_id, text=f"{message_text}", reply_markup=reply_markup
                )
                message_ids.append(message.message_id)
                actual_chat_ids.append(chat_id)
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.error(f"Не удалось обновить сообщение с chat_id: {chat_id}: {e}")
                pass

        self[row_id][key] = list(zip(actual_chat_ids, message_ids))

    async def add_main_data(
        self, record_dict: dict, row_id, initiator_chat_id: str | int
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


message_manager = MessageManager()
