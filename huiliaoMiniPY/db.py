from config import config
from storage import (
    get_ai_reply as get_ai_reply_sqlite,
    get_appointment_reminder as get_appointment_reminder_sqlite,
    get_meta as get_meta_sqlite,
    get_questionnaire_detail as get_questionnaire_detail_sqlite,
    get_questionnaire_options as get_questionnaire_options_sqlite,
    get_questionnaire_report as get_questionnaire_report_sqlite,
    get_tongue_report as get_tongue_report_sqlite,
    insert_send_log as insert_send_log_sqlite,
    list_subscription_records as list_subscription_records_sqlite,
    mark_subscription_sent as mark_subscription_sent_sqlite,
    save_ai_reply as save_ai_reply_sqlite,
    save_appointment_reminder as save_appointment_reminder_sqlite,
    save_tongue_report as save_tongue_report_sqlite,
    set_meta as set_meta_sqlite,
    start_questionnaire as start_questionnaire_sqlite,
    submit_questionnaire as submit_questionnaire_sqlite,
    upsert_subscription_record as upsert_subscription_record_sqlite,
    upsert_user as upsert_user_sqlite,
    find_sendable_subscription as find_sendable_subscription_sqlite
)

# 尝试导入MySQL存储模块，如果失败则使用SQLite
try:
    from mysql_storage import (
        get_ai_reply_mysql,
        get_appointment_reminder_mysql,
        get_meta_mysql,
        get_questionnaire_detail_mysql,
        get_questionnaire_options_mysql,
        get_questionnaire_report_mysql,
        get_tongue_report_mysql,
        insert_send_log_mysql,
        list_subscription_records_mysql,
        mark_subscription_sent_mysql,
        save_ai_reply_mysql,
        save_appointment_reminder_mysql,
        save_tongue_report_mysql,
        set_meta_mysql,
        start_questionnaire_mysql,
        submit_questionnaire_mysql,
        upsert_subscription_record_mysql,
        upsert_user_mysql,
        find_sendable_subscription_mysql
    )
    mysql_available = True
except Exception as e:
    print(f"MySQL模块导入失败: {e}")
    mysql_available = False

# 获取数据库类型
def get_db_type() -> str:
    return config.get('database', {}).get('type', 'sqlite').lower()

# 检查是否使用MySQL
def use_mysql() -> bool:
    return get_db_type() == 'mysql' and mysql_available

# 统一的数据库操作函数
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
        return start_questionnaire_mysql(*args, **kwargs)
    return start_questionnaire_sqlite(*args, **kwargs)

def get_questionnaire_detail(*args, **kwargs):
    if use_mysql():
        return get_questionnaire_detail_mysql(*args, **kwargs)
    return get_questionnaire_detail_sqlite(*args, **kwargs)

def submit_questionnaire(*args, **kwargs):
    if use_mysql():
        return submit_questionnaire_mysql(*args, **kwargs)
    return submit_questionnaire_sqlite(*args, **kwargs)

def get_questionnaire_report(*args, **kwargs):
    if use_mysql():
        return get_questionnaire_report_mysql(*args, **kwargs)
    return get_questionnaire_report_sqlite(*args, **kwargs)