import mysql.connector

# MySQL 连接配置
config = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY'
}

try:
    # 连接数据库
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # 显示所有表
    cursor.execute('SHOW TABLES')
    tables = cursor.fetchall()
    
    print('Tables in miniprogramYQY:')
    for table in tables:
        print(table[0])
    
    # 检查 ai_reply_records 表是否存在
    cursor.execute("SHOW TABLES LIKE 'ai_reply_records'")
    ai_reply_table = cursor.fetchone()
    print('\nai_reply_records table exists:', ai_reply_table is not None)
    
    # 关闭连接
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
