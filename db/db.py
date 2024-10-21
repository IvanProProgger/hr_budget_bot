import asyncpg
from config.config import Config
from helper.logging_config import logger


class ApprovalDB:
    """База данных для хранения данных о заявке"""

    def __init__(self):
        self.db_params = {
            "host": Config.db_host,
            "port": Config.db_port,
            "database": Config.db_name,
            "user": Config.db_user,
            "password": Config.db_password,
        }

    async def __aenter__(self) -> "ApprovalDB":
        self._conn = await asyncpg.connect(**self.db_params)
        logger.info("Соединение с PostgreSQL установлено.")
        return self

    async def __aexit__(self, exc_type: any, exc_val: any, exc_tb: any) -> bool:
        if exc_type:
            logger.error(f"Произошла ошибка: {exc_type}; {exc_val}; {exc_tb}")
        if self._conn:
            await self._conn.close()
            logger.info("Соединение с PostgreSQL разъединено.")
        return True

    async def create_table(self) -> None:
        """Создает таблицу 'hr_approvals', если она еще не существует."""
        async with self:
            await self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hr_approvals (
                    id SERIAL PRIMARY KEY,
                    amount REAL,
                    expense_item TEXT,
                    expense_group TEXT,
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
            )
        logger.info('Таблица "hr_approvals" создана или уже существует.')

    async def insert_record(self, record_dict: dict[str, any]) -> int:
        """Добавляет новую запись в таблицу 'hr_approvals'."""
        query = """
        INSERT INTO hr_approvals (amount, expense_item, expense_group, comment, period, payment_method,
            approvals_needed, approvals_received, status, approved_by, initiator_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """
        try:
            row_id = await self._conn.fetchval(query, *record_dict.values())
            logger.info("Информация о счёте успешно добавлена.")
            return row_id
        except Exception as e:
            raise RuntimeError(f"Не удалось добавить информацию о счёте: {e}")

    async def get_row_by_id(self, row_id: int) -> dict[str, any] | None:
        """Получаем словарь из названий и значений столбцов по id"""
        query = "SELECT * FROM hr_approvals WHERE id=$1"
        row = await self._conn.fetchrow(query, row_id)

        if not row:
            raise RuntimeError(f"По заданному id: {row_id} данных не найдено!")

        logger.info("Данные строки получены успешно.")
        return dict(row)  # Fetchrow returns an instance of Record.

    async def get_column_by_id(self, column_name: str, row_id: int) -> any:
        """Получает значение указанного столбца по id"""
        query = f"SELECT {column_name} FROM hr_approvals WHERE id=$1"
        value = await self._conn.fetchval(query, row_id)

        logger.info(f"Значение столбца '{column_name}' получено успешно.")
        return value

    async def update_row_by_id(self, row_id: int, updates: dict[str, any]) -> None:
        """Функция меняет значения столбцов."""
        set_clause = ", ".join(
            [f"{key} = ${i + 1}" for i, key in enumerate(updates.keys())]
        )
        values = list(updates.values()) + [row_id]

        query = f"UPDATE hr_approvals SET {set_clause} WHERE id = ${len(values)}"
        await self._conn.execute(query, *values)

        logger.info("Информация о счёте успешно обновлена.")

    async def get_record_info(self, row_id: int) -> str:
        """Получает детали конкретного счета из базы данных и форматирует их для бота."""
        record_dict = await self.get_row_by_id(row_id)

        return (
            f"Данные счета:\n"
            f'1.Сумма: {record_dict["amount"]}₽;\n'
            f'2.Статья: "{record_dict["expense_item"]}"\n'
            f'3.Группа: "{record_dict["expense_group"]}"\n'
            f'4.Комментарий: "{record_dict["comment"]}"\n'
            f'5.Даты начисления: "{", ".join(record_dict["period"].split())}"\n'
            f'6.Форма оплаты: "{record_dict["payment_method"]}"\n'
        )

    async def find_not_paid(self) -> list[dict[str, str]]:
        """Возвращает все данные по всем неоплаченным заявкам на платёж"""
        result = await self._conn.fetch(
            "SELECT * FROM hr_approvals WHERE status != $1 AND status != $2",
            "Paid",
            "Rejected",
        )

        if not result:
            return []

        logger.info("Неоплаченные счета найдены успешно.")

        return [dict(row) for row in result]  # Convert each row to dictionary
