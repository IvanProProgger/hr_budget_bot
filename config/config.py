from os import getenv

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс-конфиг для проекта"""

    telegram_bot_token: str = getenv("TELEGRAM_BOT_TOKEN")
    google_sheets_spreadsheet_id: str = getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    db_host: str = getenv("DB_HOST")
    db_port: int = int(getenv("DB_PORT", 5433))
    db_name: str = getenv("DB_NAME")
    db_user: str = getenv("DB_USER")
    db_password: str = getenv("DB_PASSWORD")
    google_sheets_credentials_file: str = getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
    google_sheets_categories_sheet_id: int = getenv("GOOGLE_SHEETS_CATEGORIES_SHEET_ID")
    google_sheets_records_sheet_id: int = getenv("GOOGLE_SHEETS_RECORDS_SHEET_ID")
    head_chat_ids: list[int] = list(map(int, getenv("HEAD_CHAT_IDS").split(",")))
    finance_chat_ids: list[int] = list(map(int, getenv("FINANCE_CHAT_IDS").split(",")))
    payment_chat_ids: list[int] = list(map(int, getenv("PAYMENT_CHAT_IDS").split(",")))
    initiator_chat_ids: list[int] = list(map(int, getenv("INITIATOR_CHAT_IDS").split(",")))
    developer_chat_id: list[int] = getenv("DEVELOPER_CHAT_ID")
    white_list: set[int] = set(map(int, getenv("WHITE_LIST").split(",")))

    DEPARTMENTS = {
        "6944709122": "initiator",
        "134103255": "initiator",
        "134103255": "head",
        "236746871": "finance",
        "191096978": "finance",
        "455256941": "payment",
        "427967346": "payment",  # также инициатор
        "939635840": "payment",  # также инициатор
        "5024126966": "payment", # также инициатор
        "594336984": "payment"
    }

    NICKNAMES = {
        "initiator": {
            "6944709122": "@Brilliant_Goddess",
            "427967346": "@Marina_Q_1907",
            "134103255": "@LiliBold",
            "939635840": "@dantanusha",
            "455256941": "@IrishkaKitty",
            "5024126966": "Еленой Фомичёвой",
            "594336984": "@Stilldaywonder",
        },
        "head": {
            "134103255": "@LiliBold",
            "594336984": "@Stilldaywonder",
        },
        "finance": {
            "236746871": "@dizher1",
            "191096978": "@ushattt",
            "594336984": "@Stilldaywonder",
        },
        "payment": {
            "455256941": "@IrishkaKitty",
            "427967346": "Мариной Жихарь",
            "939635840": "@dantanusha",
            "5024126966": "Еленой Фомичёвой",
            "594336984": "@Stilldaywonder",
        },
    }
