import mysql.connector

# 数据库连接配置
DB_CONFIG = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

def check_database_empty():
    """检查数据库是否为空"""
    try:
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("连接到 miniprogramYQY 数据库成功")
        
        # 检查数据库中所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("\n数据库中没有任何表，数据库为空")
            return
        
        print("\n数据库中的表：")
        print("| 表名 | 记录数 |")
        print("| --- | ---: |")
        
        total_records = 0
        for table in tables:
            table_name = table['Tables_in_miniprogramYQY']
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                result = cursor.fetchone()
                count = result['count'] if result else 0
                total_records += count
                print(f"| {table_name} | {count} |")
            except Exception as e:
                print(f"| {table_name} | 错误 |")
                print(f"  错误信息: {e}")
        
        print(f"\n数据库整体状态：{'空' if total_records == 0 else '非空'}")
        print(f"总记录数：{total_records}")
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database_empty()
