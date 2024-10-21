import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

import gspread_asyncio
import pandas as pd
import pytz
from google.oauth2.service_account import Credentials

from config.config import Config
from helper.logging_config import logger


async def get_today_moscow_time() -> str:
    """
    Функция для получения текущей даты

    :return: Сегодняшнюю дату.
    """

    moscow_tz = pytz.timezone("Europe/Moscow")
    today = datetime.now(moscow_tz)
    formatted_date = today.strftime("%d.%m.%Y")
    return formatted_date


async def add_record_to_google_sheet(record_dict: dict) -> None:
    """Функция для добавления строки в таблицу Google Sheet."""

    manager = GoogleSheetsManager()
    await manager.initialize_google_sheets()
    await manager.add_payment_to_sheet(record_dict)


async def construct_rows(
    payment_info: dict[str, str], today_date: str
) -> list[list[str]]:
    """
    Конструирует строки для обновления в таблице на основе информации о платеже.

    :param payment_info: Словарь с данными о платеже.
    :param today_date: Текущая дата в формате dd.mm.yyyy.
    :return: Список списков строк для добавления в таблицу.
    """

    period = payment_info["period"].split(" ")
    total_sum = Decimal(payment_info["amount"]) / Decimal(len(period))
    rounded_sum = float(
        total_sum.quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)
    )

    return [
        [
            today_date,
            rounded_sum,
            payment_info["item"],
            payment_info["groupment"],
            "",
            "",
            payment_info["comment"],
            month,
            payment_info["payment_method"],
        ]
        for month in period
    ]


async def apply_formatting(worksheet) -> None:
    """
    Применяет необходимое форматирование к таблице.

    :param worksheet: Рабочий лист Google Sheets.
    """

    text_format = {"textFormat": {"fontFamily": "Lato"}}
    date_format = {"numberFormat": {"type": "DATE", "pattern": "dd.mm.yyyy"}}
    currency_format = {"numberFormat": {"type": "CURRENCY", "pattern": "₽ #,###"}}

    await worksheet.format("B:I", text_format)
    await worksheet.format("B3:B", date_format)
    await worksheet.format("C3:C", currency_format)
    await worksheet.format("J3:J", date_format)


async def detect_start_row(all_data: list[list[str]]) -> int:
    """
    Определяет начальную строку для новых данных на основе существующих данных в таблице.

    :param all_data: Все данные из таблицы.
    :return: Номер первой пустой строки.
    """

    return next(
        (
            index + 1
            for index, row in enumerate(all_data)
            if all(cell == "" for cell in row[:10])
        ),
        len(all_data) + 1,
    )


async def construct_category_data(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Организует данные о категориях в структурированный словарь и список уникальных элементов.

    :param df: DataFrame с данными о категориях.
    :return: Словарь с категориями и список уникальных элементов.
    """

    data_structure = {}
    unique_items = df["Статья"].unique().tolist()

    for _, row in df.iterrows():
        category = row["Статья"]
        group = row["Группа"]

        if category not in data_structure:
            data_structure[category] = []

        if group not in data_structure[category]:
            data_structure[category].append(group)

    return data_structure, unique_items


async def update_worksheet(
    worksheet, rows_to_update: list[list[str]], start_row: int
) -> None:
    """
    Обновляет таблицу с новыми данными и применяет форматирование.

    :param worksheet: Работа лист Google Sheets.
    :param rows_to_update: Список строк для обновления.
    :param start_row: Номер первой строки для обновления.
    """

    await worksheet.update(
        f"B{start_row}:K{start_row + len(rows_to_update) - 1}",
        rows_to_update,
        value_input_option="USER_ENTERED",
    )
    logger.info(f"Добавлено {len(rows_to_update)} row, начиная с строки {start_row}")

    await apply_formatting(worksheet)


class GoogleSheetsManager:
    """Класс для обработки Google Sheets таблиц."""

    def __init__(self):
        """Инициализирует класс GoogleSheetsManager."""

        self.sheets_spreadsheet_id = Config.google_sheets_spreadsheet_id
        self.records_sheet_id = Config.google_sheets_records_sheet_id
        self.categories_sheet_id = Config.google_sheets_categories_sheet_id
        self.options_dict = None
        self.items = None
        self.agc = None

    @staticmethod
    def get_credentials() -> Credentials:
        """
        Получает учетные данные для доступа к Google Sheets API.

        :return: Объект Credentials с необходимыми разрешениями.
        """

        credentials_string = Config.google_sheets_credentials_file
        credentials_data = json.loads(credentials_string)

        creds = Credentials.from_service_account_info(credentials_data)
        return creds.with_scopes(
            [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        )

    async def initialize_google_sheets(self) -> gspread_asyncio.AsyncioGspreadClient:
        """
        Инициализирует асинхронный клиент для работы с Google Sheets.

        :return: Асинхронный клиент для работы с Google Sheets.
        """

        try:
            agcm = gspread_asyncio.AsyncioGspreadClientManager(self.get_credentials)
            self.agc = await agcm.authorize()
            logger.info("Успешная авторизация Google Sheets.")
            return self.agc
        except Exception as e:
            logger.error(f"Авторизация не удалась: {e}")
            raise RuntimeError(f"Авторизация не удалась: {e}")

    async def add_payment_to_sheet(self, payment_info: dict[str, str]) -> None:
        """
        Добавляет информацию о платеже в таблицу Google Sheets.

        :param payment_info: Словарь с данными о платеже.
        """

        try:
            spreadsheet = await self.agc.open_by_key(self.sheets_spreadsheet_id)
            worksheet = await spreadsheet.get_worksheet_by_id(self.records_sheet_id)
            all_data = await worksheet.get_all_values()
            today_date = await get_today_moscow_time()
            rows_to_update = await construct_rows(payment_info, today_date)
            start_row = await detect_start_row(all_data)

            if rows_to_update:
                await update_worksheet(worksheet, rows_to_update, start_row)

        except Exception as e:
            logger.error(f"Не удалось добавить платеж в таблицу: {e}")
            raise RuntimeError(f"Не удалось добавить платеж в таблицу: {e}")

    async def get_data(self) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
        """
        Получает статью, группу и партнёров Google Sheets в виде структурированного словаря и списка
        уникальных элементов.

        :return: Кортеж с словарем категорий и списком уникальных элементов.
        """

        try:
            spreadsheet = await self.agc.open_by_key(self.sheets_spreadsheet_id)
            worksheet = await spreadsheet.get_worksheet_by_id(self.categories_sheet_id)
            all_values = await worksheet.get_all_values()
            if all_values:
                filtered_values = [row[:2] for row in all_values[1:]]
            else:
                filtered_values = []
            df = pd.DataFrame(filtered_values, columns=["Статья", "Группа"])
            df.dropna(subset=["Статья", "Группа"], inplace=True)

            return await construct_category_data(df)
        except Exception as e:
            logger.error(f"Не удалось прочитать данные категорий: {e}")
            raise RuntimeError(f"Не удалось прочитать данные категорий: {e}")
