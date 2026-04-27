import sqlite3
import argparse

def export_table_to_sql(sqlite_db, table_name, output_file):
    print(f"导出表 {table_name} 到 SQL 文件...")
    
    # 连接SQLite
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # 获取数据
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    print(f"找到 {len(rows)} 条记录")
    
    # 生成SQL
    with open(output_file, 'a', encoding='utf-8') as f:
        # 生成INSERT语句
        for row in rows:
            # 处理值
            values = []
            for val in row:
                if val is None:
                    values.append('NULL')
                elif isinstance(val, str):
                    # 转义引号
                    val = val.replace("'", "''")
                    values.append(f"'{val}'")
                else:
                    values.append(str(val))
            
            # 生成INSERT语句
            columns_str = ', '.join([f'`{col}`' for col in column_names])
            values_str = ', '.join(values)
            insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_str});\n"
            f.write(insert_sql)
    
    # 关闭连接
    cursor.close()
    conn.close()
    
    print(f"表 {table_name} 导出完成")

def main():
    parser = argparse.ArgumentParser(description='SQLite 数据导出为 MySQL SQL 文件')
    parser.add_argument('--output', default='migrate_data.sql', help='输出SQL文件路径')
    args = parser.parse_args()
    
    # 要导出的表
    tables = [
        # mini_program.db 中的表
        ('data/mini_program.db', 'app_meta'),
        ('data/mini_program.db', 'mini_program_users'),
        ('data/mini_program.db', 'subscription_records'),
        ('data/mini_program.db', 'subscription_send_logs'),
        ('data/mini_program.db', 'ai_reply_records'),
        ('data/mini_program.db', 'tongue_report_records'),
        ('data/mini_program.db', 'appointment_reminders'),
        # 问卷相关表
        ('data/mini_program.db', 'crm_questionnaire_template'),
        ('data/mini_program.db', 'crm_questionnaire_template_subject'),
        ('data/mini_program.db', 'crm_questionnaire_user_record'),
        ('data/mini_program.db', 'crm_questionnaire_user_subject_record'),
        ('data/mini_program.db', 'crm_questionnaire_user_submit_result'),
        ('data/mini_program.db', 'crm_questionnaire_user_submit_result_analysis')
    ]
    
    # 清空输出文件
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write('-- MySQL 数据导入脚本\n')
        f.write('-- 导出自 SQLite 数据库\n\n')
    
    print(f"开始导出数据到 {args.output}...")
    
    for sqlite_db, table in tables:
        try:
            export_table_to_sql(sqlite_db, table, args.output)
        except Exception as e:
            print(f"导出表 {table} 时出错: {str(e)}")
            continue
    
    print(f"\n数据导出完成！SQL 文件已保存到 {args.output}")

if __name__ == '__main__':
    main()