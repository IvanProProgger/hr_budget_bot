import re

from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

from config.config import Config
from helper.logging_config import logger
from helper.user_data import get_nickname
from helper.utils import validate_period_dates
from src.handlers import submit_record_command
from src.sheets import GoogleSheetsManager

(
    INPUT_SUM,
    INPUT_ITEM,
    INPUT_GROUP,
    INPUT_COMMENT,
    INPUT_DATES,
    INPUT_PAYMENT_TYPE,
    CONFIRM_COMMAND,
) = range(7)

payment_types: list[str] = ["нал", "безнал", "крипта"]


async def enter_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога. Ввод суммы и получение данных о статьях, группах, партнёрах."""

    # получаем chat_id отправителя команды /enter_record;
    # проверяем входит ли он в список инициаторов.
    context.user_data["initiator_chat_id"] = update.effective_chat.id
    if context.user_data["initiator_chat_id"] not in Config.initiator_chat_ids:
        await update.message.reply_text(
            "Команда запрещена! Вы не находитесь в списке инициаторов."
        )
        return ConversationHandler.END

    # авторизуемся в Google Sheets, сохраняем данные о статьях, группах, партнёрах из таблицы "категории".
    manager = GoogleSheetsManager()
    await manager.initialize_google_sheets()
    context.user_data["options"], context.user_data["items"] = await manager.get_data()

    # отправляем сообщение "Введите сумму" от бота и сохраняем данные о нём.
    bot_message = await context.bot.send_message(
        chat_id=context.user_data["initiator_chat_id"],
        text="Введите сумму:",
        reply_markup=ForceReply(selective=True),
    )
    context.user_data["enter_sum_message_id"] = bot_message.message_id

    return INPUT_SUM


async def input_sum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода суммы и выбор категории."""

    # удаляем сообщение "Введите сумму" и данные о нём;
    # получаем, сохраняем и проверяем введённую пользователем сумму;
    # удаляем сообщение от пользователя с введённой суммой.

    await context.bot.delete_message(
        context.user_data["initiator_chat_id"],
        context.user_data["enter_sum_message_id"],
    )
    del context.user_data["enter_sum_message_id"]
    context.user_data["sum"] = update.message.text
    logger.info(f"Введена сумма {context.user_data["sum"]}")

    # проверяем введённую пользователем сумму на соответствие паттерну;
    # удаляем сообщение от пользователя с введённой суммой
    # если сумма не соответствует паттерну бот повторно отправляет сообщение с просьбой ввести сумму.
    pattern = r"^[0-9]+(?:\.[0-9]+)?$"
    await update.message.from_user.delete_message(update.message.message_id)
    if not re.fullmatch(pattern, context.user_data["sum"]):
        await update.message.reply_text("Некорректная сумма. Попробуйте ещё раз.")
        bot_message = await update.message.reply_text(
            "Введите сумму:",
            reply_markup=ForceReply(selective=True),
        )
        context.user_data["enter_sum_message_id"] = bot_message.message_id
        return INPUT_SUM

    # отправляем сообщение с валидированной суммой от бота;
    # создаём клавиатуру со статьями расхода и отправляем сообщение "Выберите статью расхода" с клавиатурой от бота.

    await update.message.reply_text(f"Введена сумма: {context.user_data["sum"]}")
    reply_markup = await create_keyboard(context.user_data["items"])
    await update.message.reply_text(
        "Выберите статью расхода:", reply_markup=reply_markup
    )

    return INPUT_ITEM


async def input_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора категории счёта."""

    # получаем и сохраняем выбранную статью расхода;
    # удаляем данные о статьях расхода
    query = update.callback_query
    selected_item = context.user_data["items"][int(query.data)]
    context.user_data["item"] = selected_item

    # изменяем сообщение от бота на выбрана статья расхода "{Статья}" и выводим выбранную статью в логи;
    logger.info(f"Выбрана статья расхода: {selected_item}")
    await query.edit_message_text(f"Выбрана статья расхода: {selected_item}")

    # из введённой статьи расхода получаем и сохраняем список групп расхода;
    # удаляем список статей из данных временного хранения
    context.user_data["groups"] = context.user_data["options"].get(selected_item)
    del context.user_data["items"]

    # если по данной статье всего одна группа расхода - выбираем группу и сохраняем данные о ней;
    # удаляем лишные данные временного хранения, отправляем сообщение инициатору с выбранной группой,
    # выводим группу в лог;
    # переходим на этап ввода комментария.
    if len(context.user_data["groups"]) == 1:
        selected_group = context.user_data["groups"][0]
        logger.info(f"Выбрана группа расхода: {selected_group}")
        context.user_data["group"] = selected_group
        del context.user_data["options"]
        del context.user_data["groups"]
        await context.bot.send_message(
            context.user_data["initiator_chat_id"],
            f"Выбрана группа расхода: {selected_group}",
        )
        return INPUT_COMMENT

    # создаём клавиатуру с группами расхода и отправляем сообщение с просьбой выбрать группу расхода инициатору
    reply_markup = await create_keyboard(context.user_data["groups"])
    await query.message.reply_text(
        "Выберите группу расхода:", reply_markup=reply_markup
    )

    return INPUT_GROUP


async def input_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора группы расходов."""

    query = update.callback_query
    context.user_data["group"] = context.user_data["groups"][int(query.data)]
    logger.info(f"Выбрана группа расхода: {context.user_data["group"]}")
    await query.edit_message_text(
        f"Выбрана группа расхода: {context.user_data["group"]}"
    )

    del context.user_data["options"]
    del context.user_data["groups"]

    bot_message = await context.bot.send_message(
        chat_id=context.user_data["initiator_chat_id"],
        text="Введите комментарий для отчёта:",
        reply_markup=ForceReply(selective=True),
    )
    context.user_data["enter_comment_message_id"] = bot_message.message_id

    return INPUT_COMMENT


async def input_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода комментария к счёту и создание цитирования для ввода дат"""

    await context.bot.delete_message(
        context.user_data["initiator_chat_id"],
        context.user_data["enter_comment_message_id"],
    )
    del context.user_data["enter_comment_message_id"]
    context.user_data["comment"] = update.message.text
    logger.info(f"Введён комментарий {context.user_data["comment"]}")

    pattern = r"^\S.*"
    await update.message.from_user.delete_message(update.message.message_id)
    if not re.fullmatch(pattern, context.user_data["comment"]):
        await update.message.reply_text(
            "Недопустимый формат комментария. Попробуйте ещё раз."
        )
        bot_message = await update.message.reply_text(
            "Введите комментарий:",
            reply_markup=ForceReply(selective=True),
        )
        context.user_data["enter_comment_message_id"] = bot_message.message_id
        return INPUT_COMMENT

    await update.message.reply_text(
        f"Введён комментарий: {context.user_data["comment"]}"
    )
    bot_message = await context.bot.send_message(
        chat_id=context.user_data["initiator_chat_id"],
        text='Введите месяц и год начисления счёта строго через пробел в формате mm.yy (Например:\n "09.22 11.22"):',
        reply_markup=ForceReply(selective=True),
    )
    context.user_data["enter_date_message_id"] = bot_message.message_id

    return INPUT_DATES


async def input_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода дат начисления счёта и создание кнопок для выбора типа оплаты"""

    # удаляем сообщение от бота "Введите месяц и год начисления" и данные о нём
    # получаем и проверяем сообщение пользователя на соответствие паттерну

    await context.bot.delete_message(
        context.user_data["initiator_chat_id"],
        context.user_data["enter_date_message_id"],
    )
    del context.user_data["enter_date_message_id"]
    context.user_data["dates"] = update.message.text
    context.user_data["dates_readable"] = ", ".join(context.user_data["dates"].split())

    # проверяем введённые даты на соответствие паттерну;
    # при несоответствии бот отправляет сообщение с просьбой ввести даты заново
    pattern = r"(\d{2}\.\d{2}\s*)+"
    match = re.search(pattern, context.user_data["dates"])
    if not re.fullmatch(pattern, context.user_data["dates"]):
        await update.message.reply_text("Неверный формат дат. Попробуйте ещё раз.")
        bot_message = await update.message.reply_text(
            'Введите месяц и год начисления счёта строго через пробел в формате mm.yy (Например:\n "09.22 11.22"):',
            reply_markup=ForceReply(selective=True),
        )
        context.user_data["enter_date_message_id"] = bot_message.message_id
        return INPUT_DATES

    # проверяем введённые даты: пытаемся преобразовать даты в реальную дату с помощью библиотеки datetime;
    # при невозможности перевести в реальную дату бот отправляет сообщение с просьбой повторно ввести дату
    try:
        period_dates = match.group(0)
        await validate_period_dates(period_dates)
    except Exception as e:
        await update.message.reply_text(
            f"Неверный формат дат. Попробуйте ещё раз. Ошибка: {e}"
        )
        bot_message = await update.message.reply_text(
            'Введите месяц и год начисления счёта строго через пробел в формате mm.yy (Например:\n "09.22 11.22"):',
            reply_markup=ForceReply(selective=True),
        )
        context.user_data["enter_date_message_id"] = bot_message.message_id
        return INPUT_DATES

    # сохраняем и логируем сообщение с введёнными пользователем датами;
    # бот пишет введённые даты в чат;
    # удаляем сообщение от пользователя с введёнными датами;
    # отправляем сообщение с клавиатурой о выборе типа оплаты

    logger.info(f"Введены даты: {context.user_data["dates_readable"]}")
    await update.message.reply_text(
        f"Введены даты: {context.user_data["dates_readable"]}"
    )
    await update.message.from_user.delete_message(update.message.message_id)
    reply_markup = await create_keyboard(payment_types)
    await update.message.reply_text("Выберите тип оплаты:", reply_markup=reply_markup)

    return INPUT_PAYMENT_TYPE


async def input_payment_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора типа оплаты и создание итогового сообщения для подтверждения или отклонения счёта"""

    query = update.callback_query
    await query.answer()
    payment_type = payment_types[int(query.data)]
    await query.edit_message_text(f"Выбран тип оплаты: {payment_type}")
    logger.info(f"Выбран тип оплаты: {payment_type}")

    context.user_data["final_command"] = (
        f"{context.user_data['sum']}; {context.user_data['item']}; "
        f"{context.user_data['group']}; {context.user_data['comment']}; "
        f"{context.user_data['dates']}; {payment_type}"
    )

    buttons = [
        [InlineKeyboardButton("Подтвердить", callback_data="Подтвердить")],
        [InlineKeyboardButton("Отмена", callback_data="Отмена")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    context.user_data["initiator_message"] = await context.bot.send_message(
        chat_id=context.user_data["initiator_chat_id"],
        text=(
            f"Получена информация о счёте:\n"
            f"1. Сумма: {context.user_data['sum']}₽\n"
            f'2. Статья: "{context.user_data['item']}"\n'
            f'3. Группа: "{context.user_data['group']}"\n'
            f'4. Комментарий: "{context.user_data['comment']}"\n'
            f'5. Даты начисления: "{context.user_data["dates_readable"]}"\n'
            f'6. Форма оплаты: "{payment_type}"\n'
            f"Проверьте правильность введённых данных!"
        ),
        reply_markup=reply_markup,
    )

    return CONFIRM_COMMAND


async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик подтверждения и отклонения итоговой команды."""

    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    initiator_id = query.from_user.id
    if query.data == "Подтвердить":
        context.args = context.user_data.get("final_command").split()
        context.bot_data["initiator_message"] = [
            (initiator_id, context.user_data["initiator_message"].message_id)
        ]
        context.user_data.clear()
        initiator_nickname = await get_nickname("initiator", initiator_id)
        logger.info(f"Счёт создан инициатором: {initiator_nickname}")
        await submit_record_command(update, context)
        return ConversationHandler.END

    elif query.data == "Отмена":
        context.user_data.clear()
        context.bot_data.clear()
        logger.info(f"Ввод счёта отменён инициатором @{query.from_user.username}")
        await stop_dialog(update, context)
        return ConversationHandler.END


async def create_keyboard(massive: list[str]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками, имеющими названия элементов массива, располагая их горизонтально.

    :param massive: Список строк для кнопок
    :return: InlineKeyboardMarkup объект
    """

    keyboard = []
    for number, item in enumerate(massive):
        button = InlineKeyboardButton(item, callback_data=number)
        keyboard.append([button])

    return InlineKeyboardMarkup(keyboard)


async def stop_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /stop."""
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Диалог был остановлен. Начните заново с командой /enter_record",
    )
    context.user_data.clear()
    context.bot_data.clear()

    return ConversationHandler.END
