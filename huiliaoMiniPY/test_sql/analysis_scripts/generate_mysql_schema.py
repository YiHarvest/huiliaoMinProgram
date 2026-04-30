def generate_mysql_schema():
    tables = [
        {
            'name': 'app_meta',
            'columns': [
                {'name': 'key', 'type': 'VARCHAR(255)', 'primary_key': True},
                {'name': 'value', 'type': 'TEXT'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'mini_program_users',
            'columns': [
                {'name': 'user_id', 'type': 'VARCHAR(255)', 'primary_key': True},
                {'name': 'openid', 'type': 'VARCHAR(255)'},
                {'name': 'session_key', 'type': 'VARCHAR(255)'},
                {'name': 'unionid', 'type': 'VARCHAR(255)'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'subscription_records',
            'columns': [
                {'name': 'id', 'type': 'INT', 'primary_key': True, 'auto_increment': True},
                {'name': 'user_id', 'type': 'VARCHAR(255)'},
                {'name': 'openid', 'type': 'VARCHAR(255)'},
                {'name': 'template_id', 'type': 'VARCHAR(255)'},
                {'name': 'scene', 'type': 'VARCHAR(255)'},
                {'name': 'subscribe_status', 'type': 'VARCHAR(50)'},
                {'name': 'accepted_at', 'type': 'VARCHAR(32)'},
                {'name': 'last_sent_at', 'type': 'VARCHAR(32)'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'subscription_send_logs',
            'columns': [
                {'name': 'id', 'type': 'INT', 'primary_key': True, 'auto_increment': True},
                {'name': 'openid', 'type': 'VARCHAR(255)'},
                {'name': 'template_id', 'type': 'VARCHAR(255)'},
                {'name': 'scene', 'type': 'VARCHAR(255)'},
                {'name': 'biz_id', 'type': 'VARCHAR(255)'},
                {'name': 'page_path', 'type': 'VARCHAR(255)'},
                {'name': 'payload', 'type': 'TEXT'},
                {'name': 'send_status', 'type': 'VARCHAR(50)'},
                {'name': 'errcode', 'type': 'VARCHAR(50)'},
                {'name': 'errmsg', 'type': 'TEXT'},
                {'name': 'sent_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'ai_reply_records',
            'columns': [
                {'name': 'reply_id', 'type': 'VARCHAR(255)', 'primary_key': True},
                {'name': 'user_id', 'type': 'VARCHAR(255)'},
                {'name': 'openid', 'type': 'VARCHAR(255)'},
                {'name': 'assistant_id', 'type': 'VARCHAR(255)'},
                {'name': 'question', 'type': 'TEXT'},
                {'name': 'content', 'type': 'TEXT'},
                {'name': 'chat_id', 'type': 'VARCHAR(255)'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'tongue_report_records',
            'columns': [
                {'name': 'analysis_id', 'type': 'VARCHAR(255)', 'primary_key': True},
                {'name': 'user_id', 'type': 'VARCHAR(255)'},
                {'name': 'openid', 'type': 'VARCHAR(255)'},
                {'name': 'report_json', 'type': 'TEXT'},
                {'name': 'tips', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'appointment_reminders',
            'columns': [
                {'name': 'appointment_id', 'type': 'VARCHAR(255)', 'primary_key': True},
                {'name': 'user_id', 'type': 'VARCHAR(255)'},
                {'name': 'openid', 'type': 'VARCHAR(255)'},
                {'name': 'doctor_name', 'type': 'VARCHAR(255)'},
                {'name': 'clinic_time', 'type': 'VARCHAR(32)'},
                {'name': 'clinic_location', 'type': 'VARCHAR(255)'},
                {'name': 'remark', 'type': 'TEXT'},
                {'name': 'status', 'type': 'VARCHAR(50)'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'crm_questionnaire_template',
            'columns': [
                {'name': 'template_id', 'type': 'INT', 'primary_key': True, 'auto_increment': True},
                {'name': 'questionnaire_name', 'type': 'TEXT'},
                {'name': 'category', 'type': 'TEXT'},
                {'name': 'apply_department', 'type': 'TEXT'},
                {'name': 'group_type', 'type': 'INTEGER'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'crm_questionnaire_user_record',
            'columns': [
                {'name': 'record_id', 'type': 'INT', 'primary_key': True, 'auto_increment': True},
                {'name': 'external_user_id', 'type': 'TEXT'},
                {'name': 'template_id', 'type': 'INTEGER'},
                {'name': 'status', 'type': 'TEXT'},
                {'name': 'status_text', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'crm_questionnaire_template_subject',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                {'name': 'template_id', 'type': 'INTEGER'},
                {'name': 'subject_id', 'type': 'INTEGER'},
                {'name': 'subject_type', 'type': 'VARCHAR(32)'},
                {'name': 'subject_title', 'type': 'VARCHAR(255)'},
                {'name': 'subject_content', 'type': 'TEXT'},
                {'name': 'sort_order', 'type': 'INTEGER'},
                {'name': 'is_required', 'type': 'CHAR(1)'}
            ]
        },
        {
            'name': 'crm_questionnaire_user_subject_record',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                {'name': 'record_id', 'type': 'INTEGER'},
                {'name': 'subject_id', 'type': 'INTEGER'},
                {'name': 'answer_content', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'crm_questionnaire_user_submit_result',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                {'name': 'record_id', 'type': 'INTEGER'},
                {'name': 'total_score', 'type': 'INTEGER'},
                {'name': 'result', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        },
        {
            'name': 'crm_questionnaire_user_submit_result_analysis',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                {'name': 'record_id', 'type': 'INTEGER'},
                {'name': 'analysis', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'VARCHAR(32)'},
                {'name': 'updated_at', 'type': 'VARCHAR(32)'}
            ]
        }
    ]
    
    # 生成 SQL
    sql_statements = []
    for table in tables:
        columns_sql = []
        for col in table['columns']:
            col_sql = f"`{col['name']}` {col['type']}"
            if col.get('primary_key'):
                col_sql += " PRIMARY KEY"
            if col.get('auto_increment'):
                col_sql += " AUTO_INCREMENT"
            columns_sql.append(col_sql)
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS `{table['name']}` (\n    "
        create_table_sql += ",\n    ".join(columns_sql)
        create_table_sql += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
        sql_statements.append(create_table_sql)
    
    return "\n\n".join(sql_statements)

# 输出 SQL
print(generate_mysql_schema())