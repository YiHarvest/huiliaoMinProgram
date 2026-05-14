from config import config

DB_TYPE = config.get('database', {}).get('type', 'sqlite').lower()
mysql_available = False

if DB_TYPE == 'mysql':
    try:
        from chat_session_storage import (
            delete_chat_session_mysql,
            get_chat_session_mysql,
            list_chat_messages_mysql,
            list_chat_sessions_mysql,
            save_chat_message_mysql,
            upsert_chat_session_mysql,
        )
        from mysql_storage import (
            find_sendable_subscription_mysql,
            get_ai_reply_mysql,
            get_appointment_reminder_mysql,
            get_doctors_list_mysql,
            get_doctor_questionnaires_by_doctor_mysql,
            get_meta_mysql,
            get_questionnaire_detail_with_binding_mysql,
            get_questionnaire_record_detail_mysql,
            get_questionnaire_options_mysql,
            get_questionnaire_report_mysql,
            insert_send_log_mysql,
            list_subscription_records_mysql,
            list_questionnaire_records_mysql,
            mark_subscription_sent_mysql,
            save_ai_reply_mysql,
            save_appointment_reminder_mysql,
            set_meta_mysql,
            start_questionnaire_with_binding_mysql,
            submit_questionnaire_with_binding_mysql,
            upsert_subscription_record_mysql,
            upsert_user_mysql,
        )
        from reminder_storage import (
            disable_tongue_reminder_mysql,
            get_tongue_reminder_status_mysql,
            list_due_tongue_reminders_mysql,
            mark_tongue_reminder_sent_mysql,
            upsert_tongue_reminder_mysql,
        )
        from database.tongue_repository import (
            count_tongue_reports as count_tongue_reports_mysql,
            get_tongue_report as get_tongue_report_mysql,
            list_tongue_reports as list_tongue_reports_mysql,
            save_tongue_report as save_tongue_report_mysql,
        )
        mysql_available = True
    except Exception as e:
        print(f"MySQL模块导入失败: {e}")
        DB_TYPE = 'sqlite'

if DB_TYPE != 'mysql':
    from chat_session_storage import (
        delete_chat_session_sqlite_wrapper as delete_chat_session_sqlite,
        get_chat_session_sqlite_wrapper as get_chat_session_sqlite,
        list_chat_messages_sqlite_wrapper as list_chat_messages_sqlite,
        list_chat_sessions_sqlite_wrapper as list_chat_sessions_sqlite,
        save_chat_message_sqlite_wrapper as save_chat_message_sqlite,
        upsert_chat_session_sqlite_wrapper as upsert_chat_session_sqlite,
    )
    from storage import (
        count_tongue_reports as count_tongue_reports_sqlite,
        find_sendable_subscription as find_sendable_subscription_sqlite,
        get_ai_reply as get_ai_reply_sqlite,
        get_appointment_reminder as get_appointment_reminder_sqlite,
        get_meta as get_meta_sqlite,
        get_questionnaire_detail as get_questionnaire_detail_sqlite,
        get_questionnaire_options as get_questionnaire_options_sqlite,
        get_questionnaire_report as get_questionnaire_report_sqlite,
        get_tongue_report as get_tongue_report_sqlite,
        insert_send_log as insert_send_log_sqlite,
        list_subscription_records as list_subscription_records_sqlite,
        list_tongue_reports as list_tongue_reports_sqlite,
        mark_subscription_sent as mark_subscription_sent_sqlite,
        save_ai_reply as save_ai_reply_sqlite,
        save_appointment_reminder as save_appointment_reminder_sqlite,
        save_tongue_report as save_tongue_report_sqlite,
        set_meta as set_meta_sqlite,
        start_questionnaire as start_questionnaire_sqlite,
        submit_questionnaire as submit_questionnaire_sqlite,
        upsert_subscription_record as upsert_subscription_record_sqlite,
        upsert_user as upsert_user_sqlite,
    )


def get_db_type() -> str:
    return config.get('database', {}).get('type', 'sqlite').lower()


def use_mysql() -> bool:
    return get_db_type() == 'mysql' and mysql_available


def upsert_user(*args, **kwargs):
    if use_mysql():
        return upsert_user_mysql(*args, **kwargs)
    return upsert_user_sqlite(*args, **kwargs)


def upsert_subscription_record(*args, **kwargs):
    if use_mysql():
        return upsert_subscription_record_mysql(*args, **kwargs)
    return upsert_subscription_record_sqlite(*args, **kwargs)


def list_subscription_records(*args, **kwargs):
    if use_mysql():
        return list_subscription_records_mysql(*args, **kwargs)
    return list_subscription_records_sqlite(*args, **kwargs)


def find_sendable_subscription(*args, **kwargs):
    if use_mysql():
        return find_sendable_subscription_mysql(*args, **kwargs)
    return find_sendable_subscription_sqlite(*args, **kwargs)


def mark_subscription_sent(*args, **kwargs):
    if use_mysql():
        return mark_subscription_sent_mysql(*args, **kwargs)
    return mark_subscription_sent_sqlite(*args, **kwargs)


def insert_send_log(*args, **kwargs):
    if use_mysql():
        return insert_send_log_mysql(*args, **kwargs)
    return insert_send_log_sqlite(*args, **kwargs)


def save_ai_reply(*args, **kwargs):
    if use_mysql():
        return save_ai_reply_mysql(*args, **kwargs)
    return save_ai_reply_sqlite(*args, **kwargs)


def get_ai_reply(*args, **kwargs):
    if use_mysql():
        return get_ai_reply_mysql(*args, **kwargs)
    return get_ai_reply_sqlite(*args, **kwargs)


def save_tongue_report(*args, **kwargs):
    if use_mysql():
        return save_tongue_report_mysql(*args, **kwargs)
    return save_tongue_report_sqlite(*args, **kwargs)


def get_tongue_report(*args, **kwargs):
    if use_mysql():
        return get_tongue_report_mysql(*args, **kwargs)
    return get_tongue_report_sqlite(*args, **kwargs)


def list_tongue_reports(*args, **kwargs):
    if use_mysql():
        return list_tongue_reports_mysql(*args, **kwargs)
    return list_tongue_reports_sqlite(*args, **kwargs)


def count_tongue_reports(*args, **kwargs):
    if use_mysql():
        return count_tongue_reports_mysql(*args, **kwargs)
    return count_tongue_reports_sqlite(*args, **kwargs)


def save_appointment_reminder(*args, **kwargs):
    if use_mysql():
        return save_appointment_reminder_mysql(*args, **kwargs)
    return save_appointment_reminder_sqlite(*args, **kwargs)


def get_appointment_reminder(*args, **kwargs):
    if use_mysql():
        return get_appointment_reminder_mysql(*args, **kwargs)
    return get_appointment_reminder_sqlite(*args, **kwargs)


def get_meta(*args, **kwargs):
    if use_mysql():
        return get_meta_mysql(*args, **kwargs)
    return get_meta_sqlite(*args, **kwargs)


def set_meta(*args, **kwargs):
    if use_mysql():
        return set_meta_mysql(*args, **kwargs)
    return set_meta_sqlite(*args, **kwargs)


def get_questionnaire_options(*args, **kwargs):
    if use_mysql():
        return get_questionnaire_options_mysql(*args, **kwargs)
    return get_questionnaire_options_sqlite(*args, **kwargs)


def start_questionnaire(*args, **kwargs):
    if use_mysql():
        return start_questionnaire_with_binding_mysql(*args, **kwargs)
    return start_questionnaire_sqlite(*args, **kwargs)


def get_questionnaire_detail(*args, **kwargs):
    if use_mysql():
        return get_questionnaire_detail_with_binding_mysql(*args, **kwargs)
    return get_questionnaire_detail_sqlite(*args, **kwargs)


def submit_questionnaire(*args, **kwargs):
    if use_mysql():
        return submit_questionnaire_with_binding_mysql(*args, **kwargs)
    return submit_questionnaire_sqlite(*args, **kwargs)


def get_doctor_questionnaires_by_doctor(*args, **kwargs):
    if use_mysql():
        return get_doctor_questionnaires_by_doctor_mysql(*args, **kwargs)
    raise NotImplementedError('doctor questionnaire lookup is only available in MySQL mode')


def get_doctors_list(*args, **kwargs):
    if use_mysql():
        return get_doctors_list_mysql(*args, **kwargs)
    raise NotImplementedError('doctor list lookup is only available in MySQL mode')


def get_questionnaire_report(*args, **kwargs):
    if use_mysql():
        return get_questionnaire_report_mysql(*args, **kwargs)
    return get_questionnaire_report_sqlite(*args, **kwargs)


def list_questionnaire_records(*args, **kwargs):
    if use_mysql():
        return list_questionnaire_records_mysql(*args, **kwargs)
    raise NotImplementedError('questionnaire record list is only available in MySQL mode')


def get_questionnaire_record_detail(*args, **kwargs):
    if use_mysql():
        return get_questionnaire_record_detail_mysql(*args, **kwargs)
    return get_questionnaire_report_sqlite(*args, **kwargs)


def upsert_chat_session(*args, **kwargs):
    if use_mysql():
        return upsert_chat_session_mysql(*args, **kwargs)
    return upsert_chat_session_sqlite(*args, **kwargs)


def get_chat_session(*args, **kwargs):
    if use_mysql():
        return get_chat_session_mysql(*args, **kwargs)
    return get_chat_session_sqlite(*args, **kwargs)


def list_chat_sessions(*args, **kwargs):
    if use_mysql():
        return list_chat_sessions_mysql(*args, **kwargs)
    return list_chat_sessions_sqlite(*args, **kwargs)


def save_chat_message(*args, **kwargs):
    if use_mysql():
        return save_chat_message_mysql(*args, **kwargs)
    return save_chat_message_sqlite(*args, **kwargs)


def list_chat_messages(*args, **kwargs):
    if use_mysql():
        return list_chat_messages_mysql(*args, **kwargs)
    return list_chat_messages_sqlite(*args, **kwargs)


def delete_chat_session(*args, **kwargs):
    if use_mysql():
        return delete_chat_session_mysql(*args, **kwargs)
    return delete_chat_session_sqlite(*args, **kwargs)


def upsert_tongue_reminder(*args, **kwargs):
    if use_mysql():
        return upsert_tongue_reminder_mysql(*args, **kwargs)
    raise NotImplementedError('tongue reminder is only available in MySQL mode')


def disable_tongue_reminder(*args, **kwargs):
    if use_mysql():
        return disable_tongue_reminder_mysql(*args, **kwargs)
    raise NotImplementedError('tongue reminder is only available in MySQL mode')


def get_tongue_reminder_status(*args, **kwargs):
    if use_mysql():
        return get_tongue_reminder_status_mysql(*args, **kwargs)
    raise NotImplementedError('tongue reminder is only available in MySQL mode')


def list_due_tongue_reminders(*args, **kwargs):
    if use_mysql():
        return list_due_tongue_reminders_mysql(*args, **kwargs)
    raise NotImplementedError('tongue reminder is only available in MySQL mode')


def mark_tongue_reminder_sent(*args, **kwargs):
    if use_mysql():
        return mark_tongue_reminder_sent_mysql(*args, **kwargs)
    raise NotImplementedError('tongue reminder is only available in MySQL mode')
