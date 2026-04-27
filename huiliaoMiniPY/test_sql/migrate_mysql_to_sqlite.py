import pymysql
import sqlite3
import json
import os
from datetime import datetime

# MySQL连接配置
MYSQL_CONFIG = {
    'host': '117.89.185.157',
    'port': 13049,
    'user': 'jinlong',
    'password': 'jinlong@880208',
    'database': 'huiliao_dev',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# SQLite文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'data', 'questionnaire.sqlite')

# 要迁移的表（按依赖顺序排列）
TABLES = [
    'crm_questionnaire_template',
    'crm_questionnaire_template_subject',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

def connect_mysql():
    """连接MySQL数据库"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        print("[OK] 成功连接MySQL数据库")
        return conn
    except Exception as e:
        print(f"[ERROR] 连接MySQL失败: {e}")
        raise

def connect_sqlite():
    """连接SQLite数据库"""
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute('PRAGMA foreign_keys = OFF')  # 关闭外键约束，方便数据迁移
        print(f"[OK] 成功连接SQLite数据库: {SQLITE_PATH}")
        return conn
    except Exception as e:
        print(f"[ERROR] 连接SQLite失败: {e}")
        raise

def create_sqlite_tables(conn):
    """在SQLite中创建表结构"""
    cursor = conn.cursor()
    
    # 创建模板表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_questionnaire_template (
        id BIGINT PRIMARY KEY,
        questionnaire_name TEXT,
        description TEXT,
        status INTEGER,
        create_time TEXT,
        update_time TEXT,
        is_deleted INTEGER,
        create_user TEXT,
        update_user TEXT
    )''')
    
    # 创建题目表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_questionnaire_template_subject (
        id BIGINT PRIMARY KEY,
        template_id BIGINT,
        subject_title TEXT,
        subject_type INTEGER,
        subject_content TEXT,
        sort INTEGER,
        create_time TEXT,
        update_time TEXT,
        is_deleted INTEGER,
        create_user TEXT,
        update_user TEXT,
        FOREIGN KEY (template_id) REFERENCES crm_questionnaire_template(id)
    )''')
    
    # 创建用户记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_questionnaire_user_record (
        id BIGINT PRIMARY KEY,
        template_id BIGINT,
        external_user_id TEXT,
        start_time TEXT,
        submit_time TEXT,
        status INTEGER,
        create_time TEXT,
        update_time TEXT,
        is_deleted INTEGER,
        create_user TEXT,
        update_user TEXT,
        FOREIGN KEY (template_id) REFERENCES crm_questionnaire_template(id)
    )''')
    
    # 创建用户题目记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_questionnaire_user_subject_record (
        id BIGINT PRIMARY KEY,
        record_id BIGINT,
        subject_id BIGINT,
        answer TEXT,
        create_time TEXT,
        update_time TEXT,
        is_deleted INTEGER,
        create_user TEXT,
        update_user TEXT,
        FOREIGN KEY (record_id) REFERENCES crm_questionnaire_user_record(id),
        FOREIGN KEY (subject_id) REFERENCES crm_questionnaire_template_subject(id)
    )''')
    
    # 创建用户提交结果表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_questionnaire_user_submit_result (
        id BIGINT PRIMARY KEY,
        record_id BIGINT,
        result TEXT,
        create_time TEXT,
        update_time TEXT,
        is_deleted INTEGER,
        create_user TEXT,
        update_user TEXT,
        FOREIGN KEY (record_id) REFERENCES crm_questionnaire_user_record(id)
    )''')
    
    # 创建用户提交结果分析表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_questionnaire_user_submit_result_analysis (
        id BIGINT PRIMARY KEY,
        submit_result_id BIGINT,
        record_id BIGINT,
        analysis_type TEXT,
        analysis TEXT,
        create_time TEXT,
        update_time TEXT,
        is_deleted INTEGER,
        create_user TEXT,
        update_user TEXT,
        FOREIGN KEY (submit_result_id) REFERENCES crm_questionnaire_user_submit_result(id)
    )''')
    
    conn.commit()
    print("[OK] SQLite表结构创建完成")

def migrate_table(mysql_conn, sqlite_conn, table_name):
    """迁移单个表的数据"""
    mysql_cursor = mysql_conn.cursor()
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # 查询MySQL表数据
        print(f"[INFO] 开始迁移{table_name}表")
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        
        print(f"[INFO] 从MySQL读取{table_name}表: {len(rows)}条记录")
        
        if not rows:
            print(f"[INFO] {table_name}表无数据")
            return 0
        
        # 获取列名
        columns = list(rows[0].keys())
        print(f"[INFO] {table_name}表列名: {columns}")
        
        # 检查SQLite表结构
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        sqlite_columns = [col[1] for col in sqlite_cursor.fetchall()]
        print(f"[INFO] SQLite {table_name}表列名: {sqlite_columns}")
        
        # 过滤出SQLite表中存在的列
        valid_columns = [col for col in columns if col in sqlite_columns]
        print(f"[INFO] 有效列名: {valid_columns}")
        
        if not valid_columns:
            print(f"[WARN] {table_name}表无有效列名匹配")
            return 0
        
        # 构建SQLite插入语句
        placeholders = ','.join(['?'] * len(valid_columns))
        insert_sql = f"INSERT OR IGNORE INTO {table_name} ({','.join(valid_columns)}) VALUES ({placeholders})"
        print(f"[INFO] 插入SQL: {insert_sql}")
        
        # 处理数据并插入SQLite
        count = 0
        for row in rows:
            # 处理JSON字段和时间字段
            processed_row = []
            for col in valid_columns:
                value = row[col]
                if isinstance(value, (dict, list)):
                    # 处理JSON字段
                    processed_row.append(json.dumps(value, ensure_ascii=False))
                elif isinstance(value, datetime):
                    # 处理时间字段
                    processed_row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    processed_row.append(value)
            
            try:
                sqlite_cursor.execute(insert_sql, processed_row)
                count += 1
            except Exception as e:
                print(f"[WARN] 插入{table_name}数据失败: {e}")
                continue
        
        sqlite_conn.commit()
        print(f"[OK] 迁移{table_name}表: {count}条记录")
        return count
    except Exception as e:
        print(f"[ERROR] 迁移{table_name}表失败: {e}")
        return 0

def clean_data(sqlite_conn):
    """清理数据"""
    cursor = sqlite_conn.cursor()
    
    try:
        # 1. 删除subject_title为空的题目
        cursor.execute('''
        DELETE FROM crm_questionnaire_template_subject 
        WHERE subject_title IS NULL OR subject_title = ''
        ''')
        
        # 2. 删除subject_content为{}或[]的空题目
        cursor.execute('''
        DELETE FROM crm_questionnaire_template_subject 
        WHERE subject_content IS NULL OR subject_content = '{}' OR subject_content = '[]'
        ''')
        deleted_subjects = cursor.rowcount
        
        # 3. 删除名称包含"测试/test/Test"的模板
        cursor.execute('''
        DELETE FROM crm_questionnaire_template 
        WHERE questionnaire_name LIKE '%测试%' 
        OR questionnaire_name LIKE '%test%' 
        OR questionnaire_name LIKE '%Test%'
        ''')
        deleted_templates = cursor.rowcount
        
        # 4. 删除没有有效题目的模板
        cursor.execute('''
        DELETE FROM crm_questionnaire_template 
        WHERE id NOT IN (
            SELECT DISTINCT template_id 
            FROM crm_questionnaire_template_subject
        )
        ''')
        deleted_empty_templates = cursor.rowcount
        
        sqlite_conn.commit()
        print(f"[OK] 清理数据完成: 删除测试模板{deleted_templates}个, 删除无效题目{deleted_subjects}个, 删除空模板{deleted_empty_templates}个")
    except Exception as e:
        print(f"[WARN] 清理数据时出错: {e}")
        sqlite_conn.rollback()

def verify_data(sqlite_conn):
    """验证数据迁移结果"""
    cursor = sqlite_conn.cursor()
    
    print("[INFO] 验证迁移结果:")
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}条记录")
    
    # 验证清理后的数据
    cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template")
    template_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject")
    subject_count = cursor.fetchone()[0]
    
    print(f"[INFO] 清理后数据:")
    print(f"  模板数量: {template_count}")
    print(f"  题目数量: {subject_count}")
    
    # 随机抽查3条中文数据
    print("[INFO] 随机抽查中文数据:")
    # 抽查模板表
    cursor.execute("SELECT id, questionnaire_name, description FROM crm_questionnaire_template LIMIT 3")
    templates = cursor.fetchall()
    for i, template in enumerate(templates, 1):
        print(f"  模板{i}: ID={template[0]}, 名称={template[1]}, 描述={template[2]}")
    
    # 抽查题目表
    cursor.execute("SELECT id, subject_title FROM crm_questionnaire_template_subject LIMIT 3")
    subjects = cursor.fetchall()
    for i, subject in enumerate(subjects, 1):
        print(f"  题目{i}: ID={subject[0]}, 标题={subject[1]}")
    
    return template_count, subject_count

def main():
    """主函数"""
    try:
        # 连接数据库
        mysql_conn = connect_mysql()
        sqlite_conn = connect_sqlite()
        
        # 创建SQLite表结构
        create_sqlite_tables(sqlite_conn)
        
        # 迁移数据
        migration_results = {}
        for table in TABLES:
            count = migrate_table(mysql_conn, sqlite_conn, table)
            migration_results[table] = count
        
        # 清理数据
        clean_data(sqlite_conn)
        
        # 验证数据
        template_count, subject_count = verify_data(sqlite_conn)
        
        # 关闭连接
        mysql_conn.close()
        sqlite_conn.close()
        
        print("[OK] 数据迁移完成!")
        return migration_results, template_count, subject_count
        
    except Exception as e:
        print(f"[ERROR] 迁移失败: {e}")
        raise

if __name__ == "__main__":
    main()
