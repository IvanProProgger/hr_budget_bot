from config.config import Config
from db import db
from helper.logging_config import logger
from helper.message_manager import message_manager
from helper.user_data import (
    get_nickname,
    get_department,
)
from helper.utils import (
    validate_period_dates,
    split_long_message,
    get_record_info,
    get_record_by_id,
    add_data_to_message_manager,
    update_storage_data,
)
from src.approval_process import (
    payment_from_head_approval_message,
    payment_from_head_and_finance_approval_message,
    finance_from_head_approval_message,
    head_from_initiator_approval_message,
    initiator_to_head_start_message,
    finance_paid_message,
    payment_paid_message,
    head_paid_message,
    initiator_paid_message,
    finance_and_head_to_payment_message,
    head_and_finance_to_payment_message,
    initiator_head_and_finance_to_payment_message,
    head_to_payment_message,
    initiator_head_to_payment_message,
    head_to_finance_message,
    initiator_head_to_finance_message,
    initiator_reject_message,
    head_reject_message,
    finance_reject_message,
)
from src.sheets import add_record_to_google_sheet
from telegram import Update
from telegram.ext import ContextTypes


async def check_access_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Проверяет, имеет ли пользователь доступ к боту.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    if update.effective_user.id not in Config.white_list:
        await update.message.reply_text("Извините, у вас нет доступа к этому боту.")
        logger.warning("В бота пытаются зайти посторонние...")
        return


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    try:
        await update.message.reply_text(
            f"<b>Бот по автоматизации заполнения бюджета</b>\n\n"
            "<i>Отправьте команду /enter_record и укажите данные счёта:</i>\n"
            "<i>1) Сумма счёта</i>\n"
            "<i>2) Статья расхода</i>\n"
            "<i>3) Группа расхода</i>\n"
            "<i>4) Дата оплаты и дата начисления платежа через пробел</i>\n"
            "<i>5) Форма оплаты</i>\n"
            "<i>6) Комментарий к платежу</i>\n\n"
            # "<i>Каждый пункт необходимо указывать строго через запятую.</i>\n\n"
            f"<b>Команды бота:</b>\n\n"
            "<i>/check <b>ID</b> - Узнать о статусе интересующего платежа</i>\n\n"
            "<i>/approve_record <b>ID</b> - Одобрить счёт</i>\n\n"
            "<i>/reject_record <b>ID</b> - Отклонить счёт</i>\n\n"
            "<i>/show_not_paid - Посмотреть необработанные платежи</i>\n\n"
            f"<i>Ваш id чата - {update.message.chat_id}</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        raise RuntimeError(f"Ошибка при отправке команды /start: {e}")


async def submit_record_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Обработчик введённых пользователем данных в соответствии с паттерном:
    Добавление платежа в базу данных 'approvals';
    Отправка данных о платеже для одобрения главой отдела.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    record_dict = await process_input(update, context)
    row_id = await add_record_to_storage(update, record_dict)

    await initiator_to_head_start_message(context, update, row_id)

    await head_from_initiator_approval_message(context, row_id)


async def process_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> dict[str, float | str | int]:
    """
    Обработчик аргументов команды /submit_record.

    :param update: Обновление чата
    :param context: Контекст бота
    :return: Словарь с данными платежа
    """

    try:
        initiator_chat_id = update.effective_chat.id
        if not context.args:
            raise ValueError("Необходимо указать данные счёта.")
        user_args = [x.strip() for x in " ".join(context.args).split(";")]
        record_dict = {
            "amount": float(user_args[0]),
            "item": user_args[1],
            "groupment": user_args[2],
            "comment": user_args[3],
            "period": await validate_period_dates(user_args[4]),
            "payment_method": user_args[5],
            "approvals_needed": 1 if float(user_args[0]) < 50000 else 2,
            "approvals_received": 0,
            "status": "Not processed",
            "approved_by": None,
            "initiator_id": initiator_chat_id,
        }
    except Exception as e:
        raise RuntimeError(
            f"Заданы неверные аргументы! Некоторые аргументы "
            f"не удалось преобразовать к ожидаемому виду. Ошибка: {e}"
        )

    return record_dict


async def add_record_to_storage(update: Update, record_dict: dict) -> int:
    """
    Добавляет запись в базу данных и обновляет данные экземпляра класса MessageManager.

    :param update: Обновление чата
    :param record_dict: Словарь с данными платежа
    :return: ID добавленной записи
    """

    try:
        initiator_chat_id = update.effective_chat.id
        async with db:
            row_id = await db.insert_record(record_dict)
    except Exception as e:
        raise RuntimeError(f"Ошибка при добавлении данных в базу данных: {e}")

    await add_data_to_message_manager(record_dict, row_id, initiator_chat_id)

    return row_id


async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатий пользователем кнопок "Одобрить" или "Отклонить."

    :param update: Обновление чата
    :param context: Контекст бота
    """

    try:
        query = update.callback_query
        _, action, department, row_id = query.data.split("_")
        row_id = int(row_id)
        approver_id = query.from_user.id
        approver = await get_nickname(department, approver_id)
    except Exception as e:
        raise RuntimeError(f'Ошибка обработки кнопок "Одобрить" и "Отклонить". {e}')

    async with db:
        record_dict = await db.get_row_by_id(row_id)
    amount = record_dict.get("amount")

    if not message_manager[row_id].get("record_data_text"):
        initiator_chat_id = record_dict.get("initiator_id")
        await add_data_to_message_manager(record_dict, row_id, initiator_chat_id)

    # распределяем данные платежа по отделам для принятия решения об одобрении
    await approval_process(
        context, action, row_id, approver, department, amount, approver_id
    )


async def approval_process(
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    row_id: int,
    approver: str,
    department: str,
    amount: float,
    approver_id: int,
) -> None:
    """
    Обработчик платежей для одобрения или отклонения.

    :param context: Контекст бота
    :param action: Действие ("approve" или "reject")
    :param row_id: ID записи в базе данных
    :param approver: Принявший решение сотрудник
    :param department: Департамент, принимающий решение
    :param amount: Сумма платежа
    :param approver_id: ID сотрудника, принявшего решение
    """

    if action == "approve":

        if department == "head" and amount >= 50000:
            await approve_to_finance_department(context, row_id, approver)

        elif department == "head" and amount < 50000:
            await approve_head_to_payment_department(context, row_id, approver)

        else:
            await approve_finance_to_payment_department(
                context, row_id, approver, approver_id
            )

    else:
        await reject_record(context, row_id, approver)


async def approve_to_finance_department(
    context: ContextTypes.DEFAULT_TYPE,
    row_id: int,
    approver: str,
) -> None:
    """
    Изменение количества апрувов и статуса платежа.
    Отправка сообщения о платеже свыше 50.000 в финансовый отдел на согласование платежа.
    Изменение сообщения от бота в чатах участников департамента "head"

    :param context: Контекст бота
    :param row_id: ID записи в базе данных
    :param approver: Сотрудник, принявший решение
    """

    # меняем статус и добавляем апрув в базу данных
    record_dict = await update_storage_data(
        row_id,
        approved_by=approver,
        status="Pending",
        approvals_received=1
    )

    # меняем или отправляем сообщение инициатору
    await initiator_head_to_finance_message(context, row_id, record_dict)

    # меняем или отправляем сообщение руководителю департамента
    await head_to_finance_message(context, row_id)

    # отправляем сообщение сотрудникам финансового отдела
    await finance_from_head_approval_message(context, row_id)


async def approve_head_to_payment_department(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, approver: str
) -> None:
    """
    Изменение статуса платежа на "Approved", изменения сообщений в чатах и отправка сообщений плательщикам.

    :param context: Контекст бота
    :param row_id: ID записи в базе данных
    :param approver: Сотрудник, принявший решение (руководитель департамента)
    """

    record_dict = await update_storage_data(
        row_id,
        approved_by=approver,
        status="Approved",
        approvals_received=1,
    )

    await initiator_head_to_payment_message(context, row_id, record_dict)

    await head_to_payment_message(context, row_id)

    payment_method = record_dict.get("payment_method")
    await payment_from_head_approval_message(context, row_id, payment_method)


async def approve_finance_to_payment_department(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, approver: str, approver_id: int
) -> None:
    """
    Изменение статуса платежа на "Approved", изменения сообщений в чатах и отправка сообщений плательщикам.

    :param context: Контекст бота
    :param row_id: ID записи в базе данных
    :param approver: Сотрудник, принявший решение (сотрудник финансового отдела)
    :param approver_id: ID сотрудника, принявшего решение
    """

    record_dict = await update_storage_data(
        row_id,
        approved_by=approver,
        status="Approved",
        approvals_received=2,
    )

    await initiator_head_and_finance_to_payment_message(context, row_id)

    await head_and_finance_to_payment_message(context, row_id)

    await finance_and_head_to_payment_message(context, row_id, approver)

    payment_method = record_dict.get("payment_method")
    await payment_from_head_and_finance_approval_message(
        context, row_id, payment_method
    )


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия кнопки "Оплачено".

    :param update: Обновление чата
    :param context: Контекст бота
    """

    try:
        query = update.callback_query
        response_list = query.data.split("_")
        row_id = int(response_list[1])
        payment_chat_id = query.from_user.id
        approver = await get_nickname("payment", query.from_user.id)
        await message_manager.update_data(row_id, {"approver": approver})
    except Exception as e:
        raise RuntimeError(f'Ошибка считывания данных с кнопки "Оплачено". Ошибка: {e}')

    await make_payment(context, row_id, payment_chat_id)


async def reject_record(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, approver: str
) -> None:
    """
    Отправка сообщения об отклонении платежа и изменение статуса платежа.

    :param context: Контекст бота
    :param row_id: ID записи в базе данных
    :param approver: Сотрудник, принявший решение о отклонении
    """

    await message_manager.update_data(row_id, {"approver": approver})
    record_dict = await update_storage_data(row_id, status="Rejected")

    await initiator_reject_message(context, row_id, record_dict)

    await head_reject_message(context, row_id)

    if record_dict.get("approvals_received") == 1:
        await finance_reject_message(context, row_id, record_dict, approver)

    del message_manager[row_id]


async def make_payment(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, payment_chat_id: int
) -> None:
    """
    Добавление записи в Google Sheets после успешного платежа.

    :param context: Контекст бота
    :param row_id: ID записи в базе данных
    :param payment_chat_id: ID чата пользователя, выполнившего оплату
    """

    record_dict = await update_storage_data(row_id, status="Paid")

    if not message_manager[row_id].get("record_data_text"):
        message_manager[row_id]["record_data_text"] = await get_record_info(record_dict)

    await initiator_paid_message(context, row_id, record_dict)

    await head_paid_message(context, row_id)

    if record_dict.get("approvals_received") == 2:
        await finance_paid_message(context, row_id, record_dict)

    await payment_paid_message(context, row_id, payment_chat_id)

    del message_manager[row_id]

    await add_record_to_google_sheet(record_dict)


async def reject_record_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Меняет в базе данных статус платежа на "Rejected" и отправляет сообщение об отмене платежа.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    row_id = context.args
    if not row_id:
        await update.message.reply_text("Пожалуйста, укажите id счёта!")
        return
    if len(row_id) > 1:
        await update.message.reply_text("Можно указать только 1 счёт!")
        return

    approver_id = str(update.effective_chat.id)
    department = await get_department(approver_id)
    if department not in ("head", "finance"):
        await update.message.reply_text("Вы не можете менять статус счёта!")
        return

    row_id = row_id[0]

    approver = await get_nickname(department, approver_id)
    async with db:
        record_dict = await db.get_row_by_id(row_id)
    if not record_dict:
        await update.message.reply_text(f"Счёт с id: {row_id} не найден.")
        return

    status = record_dict.get("status")
    if status in ("Rejected", "Paid"):
        await update.message.reply_text(f"Счёт №{row_id} уже обработан")
        return

    approvals_received = record_dict.get("approvals_received")
    if department == "head":
        if not (
            approvals_received == 0
            and status == "Not processed"
            or approvals_received == 1
            and status in ("Approved", "Pending")
        ):
            await update.message.reply_text(
                "Вы не можете отклонить данный счет! Обратитесь к сотруднику финансового отдела"
            )
            return

    elif department == "finance":
        if not (
            approvals_received == 1
            and status == "Pending"
            or approvals_received == 2
            and status == "Approved"
        ):
            await update.message.reply_text(
                "Вы не можете отклонить данный счет! Обратитесь к руководителю департамента"
            )
            return

    await message_manager.update_data(
        row_id, {"record_data_text": await get_record_info(record_dict)}
    )
    await reject_record(context, row_id, approver)
    await update.message.reply_text(f"Счёт №{row_id} отклонён!")


async def approve_record_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Добавляет согласование в зависимости от пользователя функции и запускает процесс дальнейшего согласования.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    row_id = context.args
    if len(row_id) != 1:
        await update.message.reply_text("Пожалуйста, укажите id счёта!")
        return

    try:
        row_id = int(row_id[0])
    except:
        await update.message.reply_text("Ошбика! Id счёта должен быть числом!")
        return

    record_dict = await get_record_by_id(row_id)
    if not record_dict:
        await update.message.reply_text(f"Счёт с id: {row_id} не найден.")
        return

    status = record_dict.get("status")
    if status in ("Paid", "Rejected"):
        await update.message.reply_text("Счёт уже обработан!")
        return

    approver_id = update.effective_chat.id
    department = await get_department(approver_id)

    if department not in ("head", "finance", "payment"):
        await update.message.reply_text("Вы не можете менять статус счёта!")
        return

    if department == "payment" and status != "Approved":
        await update.message.reply_text(
            "Вы можете оплачивать только подтверждённые счета!"
        )
        return

    if department == "finance" and status != "Pending":
        await update.message.reply_text(
            "Вы можете одобрять только согласованные главой департамента счета!"
        )
        return

    if department == "head" and status != "Not processed":
        await update.message.reply_text(
            "Вы можете одобрять только несогласованные счета!"
        )
        return

    action = "approve"
    amount = record_dict.get("amount")
    initiator_chat_id = record_dict.get("initiator_id")
    approver = await get_nickname(department, approver_id)
    await message_manager.update_data(row_id, {"approver": approver})

    if not message_manager[row_id].get("record_data_text"):
        await add_data_to_message_manager(record_dict, row_id, initiator_chat_id)

    if department in ("head", "finance"):
        await approval_process(
            context, action, row_id, approver, department, amount, approver_id
        )

    elif department == "payment":
        await make_payment(context, row_id, approver_id)


async def check_status_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Проверяет статус платежа по заданному ID.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    row_id = context.args
    if not row_id:
        await update.message.reply_text("Пожалуйста, укажите id счёта!")
        return

    if len(row_id) > 1:
        await update.message.reply_text("Можно указать только 1 счёт!")
        return

    record_dict = {}
    row_id = int(row_id[0])
    async with db:
        record_dict = await db.get_row_by_id(row_id)
    if not record_dict:
        await update.message.reply_text("По данному id данных не найдено!")
        return

    status = record_dict.get("status")
    approved_by = record_dict.get("approved_by")
    status_messages = {
        "Rejected": f"Счёт №{row_id} отклонён {approved_by}.",
        "Pending": f"Счёт №{row_id} одобрен {approved_by} и ожидает согласования финансового отдела.",
        "Approved": f"Счёт №{row_id} одобрен {approved_by} и ожидает оплаты.",
        "Paid": f"Счёт №{row_id} оплачен.",
        "Not processed": f"Счёт №{row_id} ожидает согласования руководителя департамента.",
    }
    status_message = status_messages.get(
        status, "Ожидается информация по статусу счёта."
    )

    await update.message.reply_text(status_message)


async def show_not_paid_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Возвращает инициатору список неоплаченных заявок на платежи из таблицы "approvals".

    :param update: Обновление чата
    :param context: Контекст бота
    """

    messages = []
    async with db:
        rows_ids = await db.find_not_paid()
        if rows_ids:
            for row_id in rows_ids:
                record_data_text = await db.get_record_info(row_id)
                messages.append(record_data_text)

    final_text = "\n".join(messages)
    if not final_text:
        await update.message.reply_text("Заявок не обнаружено")
        return

    if len(final_text) >= 4096:  # Максимальная длина сообщения в Telegram
        parts = await split_long_message(final_text)
        for part in parts:
            await update.message.reply_text(part, parse_mode="HTML")
    else:
        await update.message.reply_text(final_text, parse_mode="HTML")

    return


async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибок для логирования и отправки уведомления разработчику с детальной информацией об ошибке.

    :param update: Обновление чата
    :param context: Контекст бота
    """

    import traceback

    try:
        error_traceback = traceback.format_exc()
        message_text = f"{str(context.error)}. Трейсбек: {error_traceback}"
        if len(message_text) > 4096:
            message_to_developer = await split_long_message(message_text)
            # Отправляем каждую часть сообщения по отдельности
            for part in message_to_developer:
                await context.bot.send_message(Config.developer_chat_id, part)
        else:
            await context.bot.send_message(Config.developer_chat_id, message_text)
        logger.error(f"{message_text}\n{error_traceback}")

    except Exception as e:
        message_text = f"Ошибка при отправке уведомления об ошибке: {e}."
        logger.error(message_text, exc_info=True)
        if len(message_text) > 4096:
            message_text = await split_long_message(message_text)
            for part in message_text:
                await context.bot.send_message(Config.developer_chat_id, part)
        else:
            await context.bot.send_message(Config.developer_chat_id, message_text)
