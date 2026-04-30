import json
import mysql.connector

MYSQL_CONFIG = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

TABLES = [
    'crm_questionnaire_template',
    'crm_questionnaire_template_subject',
    'crm_subject',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

def check_table_structure():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)

    print("=" * 100)
    print("数据库真实表结构检查")
    print("=" * 100)

    for table in TABLES:
        print(f"\n### 表: {table}")
        print("-" * 80)

        # 获取列信息
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        columns = cursor.fetchall()

        print("字段列表:")
        for col in columns:
            nullable = "NULL" if col['Null'] == 'YES' else "NOT NULL"
            key = col['Key']
            extra = col['Extra']
            default = f"DEFAULT {col['Default']}" if col['Default'] else ""
            print(f"  {col['Field']:<45} {col['Type']:<25} {nullable:<10} {key:<6} {extra:<15} {default}")

        # 获取索引信息
        cursor.execute(f"SHOW INDEX FROM {table}")
        indexes = cursor.fetchall()

        if indexes:
            print("\n索引信息:")
            for idx in indexes:
                print(f"  {idx['Key_name']:<20} {idx['Column_name']:<45} {idx['Seq_in_index']} {idx['Index_type']}")

    cursor.close()
    conn.close()

def check_table_data_count():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)

    print("\n" + "=" * 100)
    print("表记录数统计")
    print("=" * 100)

    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        result = cursor.fetchone()
        print(f"{table}: {result['cnt']} 条记录")

    cursor.close()
    conn.close()

def check_sample_data():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)

    print("\n" + "=" * 100)
    print("样本数据检查（第一条记录）")
    print("=" * 100)

    # 检查模板表
    print("\n### crm_questionnaire_template 第一条:")
    cursor.execute("SELECT * FROM crm_questionnaire_template LIMIT 1")
    row = cursor.fetchone()
    if row:
        for k, v in row.items():
            print(f"  {k}: {v}")

    # 检查用户记录表
    print("\n### crm_questionnaire_user_record 第一条:")
    cursor.execute("SELECT * FROM crm_questionnaire_user_record LIMIT 1")
    row = cursor.fetchone()
    if row:
        for k, v in row.items():
            print(f"  {k}: {v}")

    # 检查题目关联表
    print("\n### crm_questionnaire_template_subject 第一条:")
    cursor.execute("SELECT * FROM crm_questionnaire_template_subject LIMIT 1")
    row = cursor.fetchone()
    if row:
        for k, v in row.items():
            print(f"  {k}: {v}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_table_structure()
    check_table_data_count()
    check_sample_data()