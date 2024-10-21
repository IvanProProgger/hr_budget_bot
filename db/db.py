import asyncpg
from config.config import Config
from helper.logging_config import logger
from helper.user_data import get_nickname


class ApprovalDB:
    """База данных для хранения данных о заявке"""

    def __init__(self):
        """
        Инициализирует объект ApprovalDB.

        Создает словарь параметров подключения к базе данных.
        """

        self.db_params = {
            "host": Config.db_host,
            "port": Config.db_port,
            "database": Config.db_name,
            "user": Config.db_user,
            "password": Config.db_password,
        }

    async def __aenter__(self) -> "ApprovalDB":
        """
        Устанавливает соединение с базой данных при входе в контекстный менеджер.

        :return: Объект ApprovalDB
        :raises Exception: При ошибке подключения
        """

        try:
            self._conn = await asyncpg.connect(**self.db_params)
            logger.info("Соединение с PostgreSQL установлено.")
            return self
        except Exception as e:
            logger.error(f"Ошибка при подключении к базе данных: {e}")
            raise

    async def __aexit__(self, exc_type: any, exc_val: any, exc_tb: any) -> bool:
        """
        Закрывает соединение с базой данных при выходе из контекстного менеджера.

        :param exc_type: Тип исключения (если возникло)
        :param exc_val: Значение исключения (если возникло)
        :param exc_tb: Трейсбэк исключения (если возникло)
        :return: True, если обработка завершена успешно
        """

        if exc_type:
            logger.error(f"Произошла ошибка: {exc_type}; {exc_val}; {exc_tb}")
        if self._conn:
            await self._conn.close()
            logger.info("Соединение с PostgreSQL разъединено.")
        return True

    async def create_table(self) -> None:
        """
        Создает таблицу 'hr_approvals', если она еще не существует.

        :return: None
        """

        async with self:
            query = """
            CREATE TABLE IF NOT EXISTS hr_approvals (
                id SERIAL PRIMARY KEY,
                amount REAL,
                item TEXT,
                groupment TEXT,
                comment TEXT,
                period TEXT,
                payment_method TEXT,
                approvals_needed INTEGER,
                approvals_received INTEGER,
                status TEXT,
                approved_by TEXT,
                initiator_id INTEGER
            )
            """
            try:
                await self._conn.execute(query)
                logger.info('Таблица "hr_approvals" создана или уже существует.')
            except Exception as e:
                logger.error(f"Ошибка при создании таблицы: {e}")
                raise

    async def insert_record(self, record_dict: dict[str, any]) -> int:
        """
        Добавляет новую запись в таблицу 'hr_approvals' и возвращает ID созданной ячейки.

        :param record_dict: Словарь с данными для добавления
        :return: ID созданной записи
        :raises RuntimeError: При ошибке добавления
        """

        query = """
        INSERT INTO hr_approvals (
            amount, item, groupment,
            comment, period, payment_method, approvals_needed,
            approvals_received, status, approved_by, initiator_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """
        try:
            row_id = await self._conn.fetchval(query, *record_dict.values())
            logger.info("Информация о счёте успешно добавлена.")
            return row_id
        except Exception as e:
            logger.error(f"Не удалось добавить информацию о счёте: {e}")
            raise RuntimeError(f"Ошибка при добавлении информации о счете: {e}")

    async def get_row_by_id(self, row_id: int) -> dict[str, any] | None:
        """
        Возвращает словарь из названий и значений столбцов по id.

        :param row_id: ID записи для получения
        :return: Словарь с данными или None, если данные не найдены
        """

        query = "SELECT * FROM hr_approvals WHERE id = $1"
        try:
            row = await self._conn.fetchrow(query, row_id)
            if row:
                logger.info("Данные строки получены успешно.")
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении строки по ID: {e}")
            raise

    async def get_value(self, column_name: str, row_id: int) -> any:
        """
        Возвращает значение указанного столбца по ID.

        :param column_name: Имя столбца для получения значения
        :param row_id: ID записи для получения значения
        :return: Значение столбца
        """

        query = f"SELECT {column_name} FROM hr_approvals WHERE id = $1"
        try:
            value = await self._conn.fetchval(query, row_id)
            logger.info(f"Значение получено успешно: {value}.")
            return value
        except Exception as e:
            logger.error(f"Ошибка при получении значения: {e}")
            raise

    async def update_row_by_id(self, row_id: int, updates: dict[str, any]) -> None:
        """
        Обновляет значения столбцов по ID.

        :param row_id: ID записи для обновления
        :param updates: Словарь с новыми значениями для обновления
        :raises Exception: При ошибке обновления
        """

        set_clause = ", ".join(f"{key} = ${i + 1}" for i, key in enumerate(updates))
        values = list(updates.values()) + [row_id]
        query = f"UPDATE hr_approvals SET {set_clause} WHERE id = ${len(values)}"
        try:
            await self._conn.execute(query, *values)
            logger.info("Успешное обновление информации о счёте.")
        except Exception as e:
            logger.error(f"Ошибка при обновлении информации о счёте: {e}")
            raise

    async def get_record_info(self, row_id: int) -> str:
        """
        Возвращает детали конкретного счета из базы данных и форматирует их для бота.

        :param row_id: ID счета для получения информации
        :return: Форматированная строка с информацией о счете
        """

        record_dict = await self.get_row_by_id(row_id)
        if not record_dict:
            return "Данные по указанному ID не найдены."

        initiator_nickname = await get_nickname(
            "initiator", record_dict["initiator_id"]
        )
        return (
            f"<b>ID счёта: {row_id}</b>\n"
            f"Данные счета:\n"
            f'1. Сумма: {record_dict["amount"]}₽\n'
            f'2. Статья: "{record_dict["item"]}"\n'
            f'3. Группа: "{record_dict["groupment"]}"\n'
            f'4. Комментарий: "{record_dict["comment"]}"\n'
            f'5. Даты начисления: "{", ".join(record_dict["period"].split())}"\n'
            f'6. Форма оплаты: "{record_dict["payment_method"]}"\n'
            f'7. Инициатор счёта: "{initiator_nickname}"\n'
        )

    async def find_not_paid(self) -> list[int]:
        """
        Возвращает список ID ячеек для неоплаченных счетов.

        :return: Список ID ячеек неоплаченных счетов
        """

        query = "SELECT id FROM hr_approvals WHERE status NOT IN ($1, $2)"
        try:
            result = await self._conn.fetch(query, "Paid", "Rejected")
            ids = [row["id"] for row in result]
            logger.info(
                f"Найдено {len(ids)} неоплаченных счетов."
                if ids
                else "Неоплаченных счетов не найдено."
            )
            return ids
        except Exception as e:
            logger.error(f"Ошибка при поиске неоплаченных счетов: {e}")
            raise
