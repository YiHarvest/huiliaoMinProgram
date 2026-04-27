import mysql.connector

config = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

tables = [
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result'
]

for table in tables:
    print(f'\n=== {table} ===')
    cursor.execute(f'SHOW COLUMNS FROM {table}')
    for col in cursor.fetchall():
        print(f'  {col["Field"]}: {col["Type"]}')

    cursor.execute(f'SELECT * FROM {table} LIMIT 1')
    row = cursor.fetchone()
    if row:
        print('  第一条数据:')
        for k, v in row.items():
            print(f'    {k}: {v}')

cursor.close()
conn.close()