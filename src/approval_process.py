from helper.message_manager import message_manager
from helper.user_data import get_chat_ids, get_chat_id_by_nickname
from helper.utils import (
    create_approval_keyboard,
    create_payment_keyboard,
    get_chat_id_by_payment_method,
)
from src.handlers import get_record_by_id
from telegram import Update
from telegram.ext import ContextTypes


async def initiator_to_head_start_message(
    context: ContextTypes.DEFAULT_TYPE, update: Update, row_id
) -> None:
    """
    Меняет сообщение в чате с инициатором после отправки сообщения руководителю департамента.

    :param context: Контекст бота
    :param update: Обновление чата
    :param row_id: ID записи для обработки
    :raises RuntimeError: При ошибке отправки сообщения
    """

    initiator_chat_id = update.effective_chat.id
    department = "initiator"
    stage = "initiator_to_head"
    if context.bot_data.get("initiator_message"):
        await message_manager.update_data(
            row_id,
            {"initiator_messages": context.bot_data.get("initiator_message")},
        )
        del context.bot_data["initiator_message"]
    try:
        if message_manager[row_id].get("initiator_messages"):
            await message_manager.resend_messages_with_tracking(
                context, row_id, department, stage, reply_markup=None
            )
        else:
            await message_manager.send_messages_with_tracking(
                context, row_id, "initiator", initiator_chat_id, "initiator_to_head"
            )
    except Exception as e:
        raise RuntimeError(f"Ошибка при изменении сообщения в чате с инициатором: {e}")


async def head_from_initiator_approval_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int
) -> None:
    """
    Отправляет сообщение на одобрение от инициатора руководителю отдела маркетинга.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    :raises RuntimeError: При ошибке отправки сообщения
    """

    try:
        department = "head"
        head_chat_id = await get_chat_ids(department)
        stage = "from_initiator"
        await message_manager.send_messages_with_tracking(
            context,
            row_id,
            department,
            head_chat_id,
            stage,
            reply_markup=await create_approval_keyboard(row_id, department),
        )
    except Exception as e:
        raise RuntimeError(
            f"Ошибка при отправке сообщения на одобрения счёта от инициатора руководителю отдела маркетинга: {e}"
        )


async def initiator_head_to_finance_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, record_dict
) -> None:
    """
    Меняет сообщение в чате с инициатором после отправки сообщения сотрудникам финансового отдела.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    :param record_dict: Словарь с данными счета
    """

    department, stage = "initiator", "head_to_finance"
    try:
        if message_manager[row_id].get("initiator_messages"):
            await message_manager.resend_messages_with_tracking(
                context, row_id, department, stage, reply_markup=None
            )
        else:
            initiator_chat_id = record_dict.get("initiator_id")
            await message_manager.send_messages_with_tracking(
                context, row_id, "initiator", initiator_chat_id, "head_to_finance"
            )
    except Exception as e:
        raise RuntimeError(
            f"Ошибка при обновлении сообщения плательщикам инициатору "
            f"после подтверждения счёта руководителем отдела маркетинга"
        )


async def head_to_finance_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int
) -> None:
    """
    Меняет сообщение в чате с руководителем отдела маркетинга после отправки сообщения сотрудникам финансового отдела.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    department, stage = "head", "head_to_finance"
    if message_manager[row_id].get("head_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, department, stage, reply_markup=None
        )
    else:
        head_chat_id = await get_chat_ids("head")
        await message_manager.send_messages_with_tracking(
            context, row_id, "head", head_chat_id, "head_to_finance"
        )


async def finance_from_head_approval_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int
) -> None:
    """
    Отправляет сообщение на одобрение сотрудникам финансового отдела
     после одобрения счёта руководителем отдела маркетинга.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    department, stage = "finance", "from_head"
    finance_chat_ids = await get_chat_ids("finance")
    await message_manager.send_messages_with_tracking(
        context,
        row_id,
        department,
        finance_chat_ids,
        stage,
        reply_markup=await create_approval_keyboard(row_id, department),
    )


async def initiator_head_and_finance_to_payment_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int
) -> None:
    """
    Меняет сообщение в чате с инициатором после согласования счёта руководителем отдела маркетинга
     и сотрудником финансового отдела и отправки сообщения на оплату счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    stage = "head_finance_to_payment"
    department = "initiator"
    if message_manager[row_id].get("initiator_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, department, stage
        )
    else:
        record_dict = await get_record_by_id(row_id)
        initiator_chat_id = record_dict.get("initiator_id")
        await message_manager.send_messages_with_tracking(
            context, row_id, "initiator", initiator_chat_id, "head_finance_to_payment"
        )


async def initiator_head_to_payment_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, record_dict: dict
) -> None:
    """
    Меняет сообщение в чате с инициатором после согласования счёта руководителем отдела маркетинга
     и отправки сообщения на оплату счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    stage = "head_to_payment"
    department = "initiator"
    if message_manager[row_id].get("initiator_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, department, stage
        )
    else:
        initiator_chat_id = record_dict.get("initiator_id")
        await message_manager.send_messages_with_tracking(
            context, row_id, "initiator", initiator_chat_id, "head_to_payment"
        )


async def head_and_finance_to_payment_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int
) -> None:
    """
    Меняет сообщение в чате с руководителем отдела маркетинга после согласования счёта руководителем отдела маркетинга
     и сотрудником финансового отдела и отправки сообщения на оплату счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    department = "head"
    stage = "head_finance_to_payment"
    if message_manager[row_id].get("head_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, department, stage
        )
    else:
        head_chat_id = await get_chat_ids("head")
        await message_manager.send_messages_with_tracking(
            context, row_id, "head", head_chat_id, "head_finance_to_payment"
        )


async def head_to_payment_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int
) -> None:
    """
    Меняет сообщение в чате с руководителем отдела маркетинга после согласования счёта руководителем отдела маркетинга
     и отправки сообщения на оплату счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    department = "head"
    stage = "head_to_payment"
    if message_manager[row_id].get("head_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, department, stage
        )
    else:
        head_chat_id = await get_chat_ids("head")
        await message_manager.send_messages_with_tracking(
            context, row_id, "head", head_chat_id, "head_to_payment"
        )


async def finance_and_head_to_payment_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, approved_by: str | int
) -> None:
    """
    Меняет сообщение в чате с сотрудником финансового отдела после согласования счёта руководителем отдела маркетинга
     и отправки сообщения на оплату счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    department = "finance"
    stage = "to_payment"
    if message_manager[row_id].get("finance_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, department, stage
        )
    else:
        approver_id = await get_chat_id_by_nickname(approved_by)
        await message_manager.send_messages_with_tracking(
            context, row_id, "finance", approver_id, "to_payment"
        )


async def payment_from_head_approval_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, payment_method: str
) -> None:
    """
    Отправляет сообщение плательщику счёта после согласования счёта руководителем отдела маркетинга.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    chat_id = await get_chat_id_by_payment_method(payment_method)
    department = "payment"
    stage = "head_to_payment"
    await message_manager.send_messages_with_tracking(
        context,
        row_id,
        department,
        chat_id,
        stage,
        reply_markup=await create_payment_keyboard(row_id),
    )


async def payment_from_head_and_finance_approval_message(
    context: ContextTypes.DEFAULT_TYPE, row_id: int, payment_method: str
) -> None:
    """
    Отправляет сообщение плательщику счёта после согласования счёта руководителем отдела маркетинга
     и сотрудником финансового отдела.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    chat_id = await get_chat_id_by_payment_method(payment_method)

    department = "payment"
    stage = "finance_to_payment"
    await message_manager.send_messages_with_tracking(
        context,
        row_id,
        department,
        chat_id,
        stage,
        reply_markup=await create_payment_keyboard(row_id),
    )


async def initiator_paid_message(
    context: ContextTypes.DEFAULT_TYPE, row_id, record_dict
) -> None:
    """
    Меняет сообщение в чате с инициатором после оплаты счёта плательщиком.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    if message_manager[row_id].get("initiator_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "initiator", "paid"
        )
    else:
        initiator_chat_id = record_dict.get("initiator_id")
        await message_manager.send_messages_with_tracking(
            context, row_id, "initiator", initiator_chat_id, "paid"
        )


async def head_paid_message(context: ContextTypes.DEFAULT_TYPE, row_id) -> None:
    """
    Меняет сообщение в чате с руководителем отдела маркетинга после оплаты счёта плательщиком.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    if message_manager[row_id].get("head_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "head", "paid"
        )
    else:
        head_chat_id = await get_chat_ids("head")
        await message_manager.send_messages_with_tracking(
            context, row_id, "head", head_chat_id, "paid"
        )


async def finance_paid_message(
    context: ContextTypes.DEFAULT_TYPE, row_id, record_dict: dict
) -> None:
    """
    Меняет сообщение в чате с сотрудником финансового отдела после оплаты счёта плательщиком.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    if message_manager[row_id].get("finance_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "finance", "paid"
        )
    else:
        finance_approver = record_dict["approved_by"].split(" и ")[1]
        finance_chat_id = await get_chat_id_by_nickname(finance_approver)
        await message_manager.send_messages_with_tracking(
            context, row_id, "finance", finance_chat_id, "paid"
        )


async def payment_paid_message(
    context: ContextTypes.DEFAULT_TYPE, row_id, payment_chat_id: int | str
) -> None:
    """
    Меняет сообщение в чате с плательщиком после оплаты счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    """

    if message_manager[row_id].get("payment_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "payment", "paid"
        )
    else:
        await message_manager.send_messages_with_tracking(
            context, row_id, "payment", payment_chat_id, "paid"
        )


async def initiator_reject_message(
    context: ContextTypes.DEFAULT_TYPE, row_id, record_dict
) -> None:
    """
    Меняет сообщение в чате с инициатором после отклонения счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    :param payment_chat_id: ID чата для отправки сообщения
    """

    if message_manager[row_id].get("initiator_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "initiator", "rejected"
        )
    else:
        initiator_chat_id = record_dict.get("initiator_id")
        await message_manager.send_messages_with_tracking(
            context, row_id, "initiator", initiator_chat_id, "rejected"
        )


async def head_reject_message(context: ContextTypes.DEFAULT_TYPE, row_id) -> None:
    """
    Меняет сообщение в чате с руководителем отдела маркетинга после отклонения счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    :param payment_chat_id: ID чата для отправки сообщения
    """

    if message_manager[row_id].get("head_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "head", "rejected"
        )
    else:
        head_chat_id = await get_chat_ids("head")
        await message_manager.send_messages_with_tracking(
            context, row_id, "head", head_chat_id, "rejected"
        )


async def finance_reject_message(
    context: ContextTypes.DEFAULT_TYPE, row_id, record_dict: dict, approver: str
) -> None:
    """
    Меняет сообщение в чате с сотрудником финансового отдела после отклонения счёта.

    :param context: Контекст бота
    :param row_id: ID записи для обработки
    :param payment_chat_id: ID чата для отправки сообщения
    """

    if message_manager[row_id].get("finance_messages"):
        await message_manager.resend_messages_with_tracking(
            context, row_id, "finance", "rejected"
        )
    else:
        finance_chat_id = await get_chat_id_by_nickname(approver)
        await message_manager.send_messages_with_tracking(
            context, row_id, "finance", finance_chat_id, "rejected"
        )
