INITIATOR = {
    "initiator_to_head": (
        "Вы добавили новый счет №{row_id}.\nСчет передан на согласование руководителю HR отдела.\n"
        "{record_data_text}"
    ),
    "head_to_finance": (
        "Счет №{row_id} одобрен руководителем HR отдела - {approver} и передан на согласование в финансовый отдел.\n"
        "{record_data_text}"
    ),
    "head_to_payment": (
        "Счет №{row_id} согласован руководителем HR отдела - {approver} и передан на оплату.\n{record_data_text}"
    ),
    "head_finance_to_payment": (
        "Счёт №{row_id} согласован руководителем HR отдела и сотрудником финансового отдела: {approver}. "
        "Счёт передан на оплату.\n{record_data_text}"
    ),
    "paid": "Счет №{row_id} оплачен {approver}.\n{record_data_text}",
    "rejected": "Счет №{row_id} отклонен {approver}.\n{record_data_text}",
}

HEAD = {
    "from_initiator": (
        "Добавлен новый счет №{row_id} от {initiator_nickname}.\nПожалуйста, одобрите счет.\n{record_data_text}"
    ),
    "head_to_finance": (
        "Вы одобрили счет №{row_id}.\nСчет передан на согласование в финансовый отдел.\n{record_data_text}"
    ),
    "head_to_payment": (
        "Вы согласовали счет №{row_id}.\nСчет передан на оплату.\n{record_data_text}"
    ),
    "head_finance_to_payment": (
        "Счет №{row_id} согласован вами и сотрудником финансового отдела: {approver}.\n"
        "Счет передан на оплату.\n{record_data_text}"
    ),
    "paid": "Счет №{row_id} оплачен {approver}.\n{record_data_text}",
    "rejected": "Счет №{row_id} отклонен {approver}.\n{record_data_text}",
}

FINANCE = {
    "from_head": (
        "Добавлен новый счет №{row_id} от {initiator_nickname}\n"
        "Счет согласован руководителем HR отдела: {approver}.\n"
        "Пожалуйста, одобрите платёж.\n{record_data_text}"
    ),
    "to_payment": (
        "Счет №{row_id} согласован вами и руководителем HR отдела: {approver}.\n"
        "Счет передан на оплату.\n{record_data_text}"
    ),
    "paid": "Счет №{row_id} оплачен {approver}.\n{record_data_text}",
    "rejected": "Счет №{row_id} отклонен {approver}.\n{record_data_text}",
}

PAYMENT = {
    "head_to_payment": (
        "Добавлен новый счет №{row_id} от {initiator_nickname}\nСчет согласован руководителем HR отдела: {approver}"
        " и готов к оплате.\nПожалуйста, оплатите счет.\n{record_data_text}"
    ),
    "finance_to_payment": (
        "Добавлен новый счет №{row_id} от {initiator_nickname}\nСчет согласован руководителем HR отдела и"
        " сотрудником финансового отдела: {approver}, и готов к оплате.\nПожалуйста, оплатите счет.\n"
        "{record_data_text}"
    ),
    "paid": "Счет №{row_id} оплачен {approver}.\n{record_data_text}",
    "rejected": "Счет №{row_id} отклонен {approver}.\n{record_data_text}",
}
