import mysql.connector
from mysql_storage import MYSQL_CONFIG

def test_mysql_connection():
    print("测试MySQL连接...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        print("MySQL连接成功！")
        
        # 测试查询
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SHOW DATABASES;")
        databases = cursor.fetchall()
        print("可用数据库:")
        for db in databases:
            print(f"  - {db['Database']}")
        
        # 测试表结构
        cursor.execute("USE miniprogramYQY;")
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("\nminiprogramYQY 表:")
        for table in tables:
            # 动态获取字段名
            table_name = list(table.values())[0]
            print(f"  - {table_name}")
        
        # 测试数据
        cursor.execute("SELECT COUNT(*) as count FROM crm_questionnaire_template;")
        result = cursor.fetchone()
        print(f"\ncrm_questionnaire_template 表数据行数: {result['count']}")
        
        cursor.close()
        connection.close()
        print("\n测试完成，MySQL连接正常！")
        return True
    except Exception as e:
        print(f"MySQL连接失败: {e}")
        return False

if __name__ == "__main__":
    test_mysql_connection()