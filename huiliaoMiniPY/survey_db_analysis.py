import pymysql

# 数据库连接信息
host = '117.89.185.157'
port = 13049
user = 'jinlong'
password = 'jinlong@880208'
db = 'huiliao_dev'

# 要分析的表
survey_tables = [
    'crm_questionnaire_template',
    'crm_questionnaire_template_subject',
    'crm_questionnaire_user',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

try:
    # 连接数据库
    print("正在连接数据库...")
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    print("数据库连接成功！")
    
    # 分析每张表
    for table_name in survey_tables:
        print(f"\n{'='*80}")
        print(f"分析表：{table_name}")
        print(f"{'='*80}")
        
        # 1. 查看表结构
        print("\n1. 表结构：")
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            structure = cursor.fetchall()
            for field in structure:
                print(f"  {field['Field']} - {field['Type']} - {field['Null']} - {field['Key']}")
        
        # 2. 查看样例数据
        print("\n2. 样例数据（最多5条）：")
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = cursor.fetchall()
            if sample_data:
                for i, row in enumerate(sample_data):
                    print(f"  记录 {i+1}:")
                    for key, value in row.items():
                        # 限制值的长度，避免输出过长
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"    {key}: {value}")
            else:
                print("  表中暂无数据")
        
        # 3. 查看索引
        print("\n3. 索引信息：")
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            indexes = cursor.fetchall()
            if indexes:
                for idx in indexes:
                    print(f"  索引名: {idx['Key_name']}, 字段: {idx['Column_name']}, 类型: {idx['Index_type']}")
            else:
                print("  无索引")
    
    # 4. 分析关联关系
    print(f"\n{'='*80}")
    print("关联关系分析")
    print(f"{'='*80}")
    
    # 查看外键关系
    print("\n外键关系：")
    with connection.cursor() as cursor:
        for table_name in survey_tables:
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table = cursor.fetchone()
            create_sql = create_table['Create Table']
            # 提取外键信息
            lines = create_sql.split('\n')
            for line in lines:
                if 'FOREIGN KEY' in line:
                    print(f"  {table_name}: {line.strip()}")
    
    print("\n数据库分析完成！")
    
finally:
    if 'connection' in locals() and connection:
        connection.close()
        print("\n数据库连接已关闭")