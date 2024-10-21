from os import getenv

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс-конфиг для проекта"""

    telegram_bot_token: str = getenv("TELEGRAM_BOT_TOKEN")
    google_sheets_spreadsheet_id: str = getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    db_host: str = getenv("DB_HOST")
    db_port: int = int(getenv("DB_PORT", 5432))
    db_name: str = getenv("DB_NAME")
    db_user: str = getenv("DB_USER")
    db_password: str = getenv("DB_PASSWORD")
    google_sheets_credentials_file: str = '{\r\n    "type":  "service_account",\r\n    "project_id":  "marketing-budget-435908",\r\n    "private_key_id":  "9db70e471c0bddce2297a2d6183e6529728a1df3",\r\n    "private_key":  "-----BEGIN PRIVATE KEY-----\\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQChzfnhSxhevJQR\\nLmC3B9BQRYZft5NJ4cDMybIiIPLw3sjcDusQCtgIAFjlzourhN9VvSQfHXiL9ovb\\nz11aoT2VKLqEz5yK5Q7dcwcEcnZ36j1Ca1KjEXc87X//CScJqWtGkN8V+BEnAmb4\\nHC54deThE2Ucw/vYpIxvxdiPDnNpzs9KcxrBs4L0EMUZgQ3hQVJC0cm1gusosTOK\\nvz95d2eDwiGAogWLzLLw+exYx0eb7Y7nJ6VTCVThcsy0lx+FoccbQzS9woJsowE3\\ni/jvaa5gNkFFooWSp+XMDlyRztheie1roz8oIbt1uG14HT9p8nCt+1+uLoZlMUl/\\nFL3ItgNzAgMBAAECgf85JGIPaLAPrbgRQf5DAnPJK1AmZkXA3XlFB/YbF3CGFLNP\\nMoEuY2AtocM3wn+oNiHApdE+zsDmrQhxpAQxIHqqyfGgr9/TLYYeDAF6EJVRrNBp\\n9fFcGdqZni9EYkiJ/hDY/dxWwvNLx97bTC/XWuKcyNP4SQ/iT669bXMZEoFqFjJ2\\n5jJW5LhleqvUK4l8qk14Tt8XDrOHhX0390hxfyLZT/WHSosBES3GuhZxuIFjGeSl\\nHYJl0Nn8fkoTD4CqlK3NzKEidNFfSYT/HwzPu5aCKQlGSwmZlpik2RaA9AKa644D\\nitaqRcukTtjl9KnnEc35f36+e/b8rGlMflhQJpUCgYEA0p40yhoNkS0wtgG7tc+f\\nu/2sCK8/g04DewplHJtxNk06R9aNqeqDCqfPzBT4XkaVvHYnVVAWet5pnOMRdm2b\\nXTN4jHlcrQ3y8AiG3gjtMhMgYqHWTQTG7aGX5buod8Vf9CYsEnm6yto4XzFn/J6f\\ngNL/NHV51E02PSX3qx8gyIUCgYEAxKsyykBtRcZPdQ70DwhvV9mezWlP92AIaEe4\\nFqOzNUEaF2FLXwqEN1ZuVx/tK/TEjxLkVP6Nfw+S5Vyxt8SD08W+4FBA5nVt1OrK\\nzBBqn2YfyEzjZ9XbQ/X6ol+fUspFMXI9B8xVax9C806aL4DJBNanLcDv9BLTsbAA\\n3Wj72ZcCgYBnQp95EqriKXi/Uzw3mDKlVWp524nVE3OLaH5IN0GbMOPJArzzuIFE\\nwR+U3BclCZAyFO+V2S0cUl0PSRhvqq9IU4rfvESep78axeNxiojYSx5OnS/XFOd+\\n7AHv5UBkcEVqCykCaeIVwEVxDmUAKrjizQ/IJWx0lOJpumqh4CIPjQKBgBQGXoCL\\neNTe8V447I7PTA8E4I+HxpWomJKNoufjOS8V9uMki/kcaAP+b/O9E3gjTxRGVyt0\\nU9H5MvrZqlrMzqN0gg/y+/i7Qjiow4dtsH2Ud238rjb3ZoEP/bokxGM4pzz2pdIy\\ncwwaPcXqXfayRUWR2anl+EjA1f9ErYHd2673AoGBAKNqXUpid7hMyfKUKnXbgSyt\\n3D8FnIl65BUWdHHnHooW1qfTIkBeU8xUz1z/H8AobNBADuk2v2uaLyj3zeRCvsuL\\nDEMa0l6kbr3H2Vzyyz9vXwiHFvvGQ/7UNuiOKmd1GFY6gBYqWU94fyW5RkzszIyc\\n5nYAeb1BvwgRYwpfFhGE\\n-----END PRIVATE KEY-----\\n",\r\n    "client_email":  "id-707@marketing-budget-435908.iam.gserviceaccount.com",\r\n    "client_id":  "114923236223627691807",\r\n    "auth_uri":  "https://accounts.google.com/o/oauth2/auth",\r\n    "token_uri":  "https://oauth2.googleapis.com/token",\r\n    "auth_provider_x509_cert_url":  "https://www.googleapis.com/oauth2/v1/certs",\r\n    "client_x509_cert_url":  "https://www.googleapis.com/robot/v1/metadata/x509/id-707%40marketing-budget-435908.iam.gserviceaccount.com",\r\n    "universe_domain":  "googleapis.com"\r\n}'
    google_sheets_categories_sheet_id: int = getenv("GOOGLE_SHEETS_CATEGORIES_SHEET_ID")
    google_sheets_records_sheet_id: int = getenv("GOOGLE_SHEETS_RECORDS_SHEET_ID")
    head_chat_ids: list[int] = list(map(int, getenv("HEAD_CHAT_IDS").split(",")))
    finance_chat_ids: list[int] = list(map(int, getenv("FINANCE_CHAT_IDS").split(",")))
    payment_chat_ids: list[int] = list(map(int, getenv("PAYMENT_CHAT_IDS").split(",")))
    initiator_chat_ids: list[int] = list(map(int, getenv("INITIATOR_CHAT_IDS").split(",")))
    developer_chat_id: list[int] = getenv("DEVELOPER_CHAT_ID")
    white_list: set[int] = set(map(int, getenv("WHITE_LIST").split(",")))

    DEPARTMENTS = {
        "180543030": "initiator",
        "113382451": "initiator",
        "482546749": "initiator",
        "523986696": "head",
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
            "180543030": "@irina_kuderova",
            "427967346": "Мариной Жихарь",
            "113382451": "@koroldorog",
            "482546749": "@bais_bais",
            "939635840": "@dantanusha",
            "5024126966": "Еленой Фомичёвой",
            "594336984": "@Stilldaywonder",
        },
        "head": {
            "180543030": "@irina_kuderova",
            "523986696": "@bonn_ya",
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
