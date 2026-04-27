import sqlite3
import mysql.connector
import argparse

# MySQL连接配置
mysql_config = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

# 表映射配置 - 只包含 mini_program.db 中的表
table_mappings = {
    'app_meta': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['key', 'value', 'updated_at']
    },
    'mini_program_users': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['user_id', 'openid', 'session_key', 'unionid', 'created_at', 'updated_at']
    },
    'subscription_records': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['id', 'user_id', 'openid', 'template_id', 'scene', 'subscribe_status', 'accepted_at', 'last_sent_at', 'created_at', 'updated_at']
    },
    'subscription_send_logs': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['id', 'openid', 'template_id', 'scene', 'biz_id', 'page_path', 'payload', 'send_status', 'errcode', 'errmsg', 'sent_at']
    },
    'ai_reply_records': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['reply_id', 'user_id', 'openid', 'assistant_id', 'question', 'content', 'chat_id', 'created_at']
    },
    'tongue_report_records': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['analysis_id', 'user_id', 'openid', 'report_json', 'tips', 'created_at']
    },
    'appointment_reminders': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['appointment_id', 'user_id', 'openid', 'doctor_name', 'clinic_time', 'clinic_location', 'remark', 'status', 'created_at', 'updated_at']
    },
    'crm_questionnaire_template': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['template_id', 'questionnaire_name', 'category', 'apply_department', 'group_type', 'created_at', 'updated_at']
    },
    'crm_questionnaire_user_record': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['record_id', 'external_user_id', 'template_id', 'status', 'status_text', 'created_at', 'updated_at']
    },
    'crm_questionnaire_template_subject': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['id', 'template_id', 'subject_id', 'subject_type', 'subject_title', 'subject_content', 'sort_order', 'is_required']
    },
    'crm_questionnaire_user_subject_record': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['id', 'record_id', 'subject_id', 'answer_content', 'created_at', 'updated_at']
    },
    'crm_questionnaire_user_submit_result': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['id', 'record_id', 'total_score', 'result', 'created_at', 'updated_at']
    },
    'crm_questionnaire_user_submit_result_analysis': {
        'sqlite_db': 'data/mini_program.db',
        'columns': ['id', 'record_id', 'analysis', 'created_at', 'updated_at']
    }
}

def migrate_table(table_name, truncate=False):
    print(f"\n=== 迁移表: {table_name} ===")
    
    # 获取表配置
    table_config = table_mappings.get(table_name)
    if not table_config:
        print(f"表 {table_name} 未配置")
        return
    
    sqlite_db = table_config['sqlite_db']
    columns = table_config['columns']
    
    # 构建SQL语句
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join([f'`{col}`' for col in columns])
    insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
    
    # 连接SQLite
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # 查询数据
        select_sql = f"SELECT {', '.join(columns)} FROM {table_name}"
        sqlite_cursor.execute(select_sql)
        rows = sqlite_cursor.fetchall()
        
        print(f"找到 {len(rows)} 条记录")
        
        if not rows:
            sqlite_cursor.close()
            sqlite_conn.close()
            return
        
        # 连接MySQL
        mysql_conn = mysql.connector.connect(**mysql_config)
        mysql_cursor = mysql_conn.cursor()
        
        # 如果需要清空表
        if truncate:
            truncate_sql = f"TRUNCATE TABLE `{table_name}`"
            mysql_cursor.execute(truncate_sql)
            mysql_conn.commit()
            print("已清空表数据")
        
        # 批量插入
        success_count = 0
        error_count = 0
        
        for i, row in enumerate(rows):
            try:
                mysql_cursor.execute(insert_sql, row)
                success_count += 1
                
                # 每100行提交一次
                if (i + 1) % 100 == 0:
                    mysql_conn.commit()
                    print(f"已迁移 {i + 1} 行")
            except Exception as e:
                error_count += 1
                print(f"第 {i + 1} 行出错: {str(e)}")
                # 继续处理下一行
                continue
        
        # 提交剩余数据
        mysql_conn.commit()
        
        print(f"迁移完成: 成功 {success_count} 条, 失败 {error_count} 条")
        
        # 关闭连接
        mysql_cursor.close()
        mysql_conn.close()
        sqlite_cursor.close()
        sqlite_conn.close()
        
        return success_count
        
    except Exception as e:
        print(f"迁移表 {table_name} 时出错: {str(e)}")
        # 确保连接关闭
        try:
            if 'sqlite_cursor' in locals():
                sqlite_cursor.close()
            if 'sqlite_conn' in locals():
                sqlite_conn.close()
            if 'mysql_cursor' in locals():
                mysql_cursor.close()
            if 'mysql_conn' in locals():
                mysql_conn.close()
        except:
            pass
        return 0

def main():
    parser = argparse.ArgumentParser(description='SQLite to MySQL 数据迁移工具')
    parser.add_argument('--truncate', action='store_true', help='迁移前清空表数据')
    parser.add_argument('--tables', nargs='+', help='指定要迁移的表')
    args = parser.parse_args()
    
    # 确定要迁移的表
    tables_to_migrate = args.tables if args.tables else list(table_mappings.keys())
    
    print("开始数据迁移...")
    print(f"MySQL连接: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
    print(f"要迁移的表: {tables_to_migrate}")
    
    total_count = 0
    table_counts = {}
    
    for table in tables_to_migrate:
        if table in table_mappings:
            count = migrate_table(table, args.truncate)
            total_count += count
            table_counts[table] = count
        else:
            print(f"跳过不存在的表: {table}")
    
    print("\n=== 迁移汇总 ===")
    for table, count in table_counts.items():
        print(f"{table}: {count} 条")
    print(f"总计: {total_count} 条")
    print("\n数据迁移完成！")

if __name__ == '__main__':
    main()