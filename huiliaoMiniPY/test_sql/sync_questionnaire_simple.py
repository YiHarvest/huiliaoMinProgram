import mysql.connector
import time

# 数据库连接配置
SOURCE_DB = {
    'host': '117.89.185.157',
    'port': 13049,
    'user': 'jinlong',
    'password': 'jinlong@880208',
    'database': 'huiliao_dev',
    'charset': 'utf8mb4'
}

TARGET_DB = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

# 需要同步的表
TABLES_TO_SYNC = [
    'crm_questionnaire_template',
    'crm_subject',
    'crm_questionnaire_template_subject',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

# 批次大小
BATCH_SIZE = 1000

def connect_db(config):
    """连接数据库"""
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        return conn, cursor
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None, None

def get_create_table_statement(cursor, table):
    """获取表的创建语句"""
    try:
        cursor.execute(f"SHOW CREATE TABLE {table}")
        result = cursor.fetchone()
        return result['Create Table'] if result else None
    except Exception as e:
        print(f"获取表 {table} 创建语句失败: {e}")
        return None

def create_table(cursor, create_statement):
    """创建表"""
    try:
        cursor.execute(create_statement)
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        return False

def check_table_exists(cursor, table):
    """检查单个表是否存在"""
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"检查表 {table} 失败: {e}")
        return False

def truncate_table(cursor, table):
    """清空表"""
    try:
        cursor.execute(f"TRUNCATE TABLE {table}")
        return True
    except Exception as e:
        print(f"清空表 {table} 失败: {e}")
        return False

def get_table_columns(cursor, table):
    """获取表的列名"""
    try:
        cursor.execute(f"DESCRIBE {table}")
        columns = [row['Field'] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        print(f"获取表 {table} 列名失败: {e}")
        return []

def get_table_row_count(cursor, table):
    """获取表的总行数"""
    try:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        result = cursor.fetchone()
        return result['count'] if result else 0
    except Exception as e:
        print(f"获取表 {table} 行数失败: {e}")
        return -1

def sync_table(source_conn, source_cursor, target_conn, target_cursor, table):
    """同步单个表"""
    try:
        # 获取源库行数
        source_count = get_table_row_count(source_cursor, table)
        if source_count == -1:
            return {}
        
        # 获取表结构
        columns = get_table_columns(source_cursor, table)
        if not columns:
            return {}
        
        # 构建SQL语句
        columns_str = ','.join(columns)
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        # 分批读取和插入
        read_count = 0
        insert_count = 0
        error_count = 0
        
        # 读取数据
        source_cursor.execute(f"SELECT {columns_str} FROM {table}")
        
        while True:
            rows = source_cursor.fetchmany(BATCH_SIZE)
            if not rows:
                break
            
            read_count += len(rows)
            
            # 准备插入数据
            batch = []
            for row in rows:
                values = [row[col] for col in columns]
                batch.append(values)
            
            # 执行批量插入
            try:
                target_cursor.executemany(insert_sql, batch)
                target_conn.commit()
                insert_count += len(batch)
            except Exception as e:
                target_conn.rollback()
                error_count += len(batch)
                print(f"插入数据失败: {e}")
                return {}
        
        return {
            'source_count': source_count,
            'read_count': read_count,
            'insert_count': insert_count,
            'error_count': error_count
        }
        
    except Exception as e:
        print(f"同步表 {table} 失败: {e}")
        return {}

def main():
    # 连接数据库
    source_conn, source_cursor = connect_db(SOURCE_DB)
    target_conn, target_cursor = connect_db(TARGET_DB)
    
    if not source_conn or not target_conn:
        print("数据库连接失败，退出")
        return
    
    try:
        # 检查并创建表
        print("=== 检查并创建表 ===")
        for table in TABLES_TO_SYNC:
            source_exists = check_table_exists(source_cursor, table)
            target_exists = check_table_exists(target_cursor, table)
            
            print(f"{table}: 源库={'存在' if source_exists else '不存在'}, 目标库={'存在' if target_exists else '不存在'}")
            
            if not target_exists:
                print(f"创建表 {table}")
                create_stmt = get_create_table_statement(source_cursor, table)
                if create_stmt:
                    success = create_table(target_cursor, create_stmt)
                    if not success:
                        print(f"创建表 {table} 失败，退出")
                        return
                else:
                    print(f"无法获取表 {table} 的创建语句，退出")
                    return
        
        # 提交创建表的事务
        target_conn.commit()
        
        # 对比表结构
        print("\n=== 对比表结构 ===")
        for table in TABLES_TO_SYNC:
            source_create = get_create_table_statement(source_cursor, table)
            target_create = get_create_table_statement(target_cursor, table)
            
            if source_create and target_create:
                consistent = source_create == target_create
                print(f"{table}: {'一致' if consistent else '不一致'}")
                if not consistent:
                    print("  源库创建语句:", source_create[:200], "...")
                    print("  目标库创建语句:", target_create[:200], "...")
            else:
                print(f"{table}: 无法获取创建语句")
        
        # 清空目标库中的表
        print("\n=== 清空目标库中的表 ===")
        for table in reversed(TABLES_TO_SYNC):
            success = truncate_table(target_cursor, table)
            if not success:
                print(f"清空表 {table} 失败，退出")
                return
        target_conn.commit()
        
        # 执行同步
        print("\n=== 执行数据同步 ===")
        sync_results = {}
        for i, table in enumerate(TABLES_TO_SYNC):
            print(f"正在同步第 {i+1}/{len(TABLES_TO_SYNC)} 张表: {table}")
            start_time = time.time()
            
            result = sync_table(source_conn, source_cursor, target_conn, target_cursor, table)
            sync_results[table] = result
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"  源库行数: {result.get('source_count', 'N/A')}")
            print(f"  读取行数: {result.get('read_count', 'N/A')}")
            print(f"  成功插入: {result.get('insert_count', 'N/A')}")
            print(f"  失败行数: {result.get('error_count', 'N/A')}")
            print(f"  耗时: {duration:.2f} 秒")
            
            if not result:
                print(f"同步失败，退出")
                return
        
        # 验证记录数
        print("\n=== 验证记录数 ===")
        print("| 表名 | 源库行数 | 目标库行数 | 是否一致 |")
        print("| --- | ---: | ---: | --- |")
        for table in TABLES_TO_SYNC:
            source_count = get_table_row_count(source_cursor, table)
            target_count = get_table_row_count(target_cursor, table)
            consistent = source_count == target_count
            print(f"| {table} | {source_count} | {target_count} | {'是' if consistent else '否'} |")
        
        # 验证 JSON 字段
        print("\n=== 验证 JSON 字段 ===")
        # 检查 crm_subject 的 subject_content 字段
        source_cursor.execute("SELECT id, subject_content FROM crm_subject ORDER BY RAND() LIMIT 3")
        source_rows = source_cursor.fetchall()
        
        for row in source_rows:
            source_value = row['subject_content']
            source_length = len(str(source_value)) if source_value is not None else 0
            
            # 在目标库中查找对应记录
            target_cursor.execute("SELECT subject_content FROM crm_subject WHERE id = %s", (row['id'],))
            target_row = target_cursor.fetchone()
            target_value = target_row['subject_content'] if target_row else None
            target_length = len(str(target_value)) if target_value is not None else 0
            
            print(f"  题目ID: {row['id']}")
            print(f"  源库长度: {source_length}")
            print(f"  目标库长度: {target_length}")
            print(f"  是否一致: {'是' if source_length == target_length else '否'}")
            print(f"  源库内容: {source_value[:200]}...")
            print(f"  目标库内容: {target_value[:200]}...")
            print()
        
        # 验证多次填写
        print("\n=== 验证多次填写 ===")
        # 查找有多次填写记录的用户
        source_cursor.execute("""
            SELECT external_user_id, questionnaire_name, COUNT(*) as submit_count 
            FROM crm_questionnaire_user_record 
            GROUP BY external_user_id, questionnaire_name 
            HAVING COUNT(*) > 1 
            LIMIT 3
        """)
        users = source_cursor.fetchall()
        
        for user in users:
            print(f"  用户: {user['external_user_id']}")
            print(f"  量表: {user['questionnaire_name']}")
            print(f"  填写次数: {user['submit_count']}")
            
            # 检查目标库中是否存在这些记录
            target_cursor.execute("""
                SELECT COUNT(*) as count 
                FROM crm_questionnaire_user_record 
                WHERE external_user_id = %s AND questionnaire_name = %s
            """, (user['external_user_id'], user['questionnaire_name']))
            target_count = target_cursor.fetchone()['count']
            print(f"  目标库记录数: {target_count}")
            print(f"  是否一致: {'是' if user['submit_count'] == target_count else '否'}")
            print()
        
        # 验证完整链路
        print("\n=== 验证完整链路 ===")
        # 随机获取一个模板
        source_cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template ORDER BY RAND() LIMIT 1")
        template = source_cursor.fetchone()
        
        if template:
            template_id = template['id']
            print(f"  模板: {template['questionnaire_name']} (ID: {template_id})")
            
            # 获取模板的题目
            source_cursor.execute("""
                SELECT COUNT(*) as count 
                FROM crm_questionnaire_template_subject 
                WHERE template_id = %s
            """, (template_id,))
            source_subject_count = source_cursor.fetchone()['count']
            
            # 检查目标库中是否存在这些记录
            target_cursor.execute("""
                SELECT COUNT(*) as count 
                FROM crm_questionnaire_template_subject 
                WHERE template_id = %s
            """, (template_id,))
            target_subject_count = target_cursor.fetchone()['count']
            print(f"  题目数: 源库={source_subject_count}, 目标库={target_subject_count}")
            
            # 获取用户记录
            source_cursor.execute("""
                SELECT id 
                FROM crm_questionnaire_user_record 
                WHERE questionnaire_name = %s 
                LIMIT 1
            """, (template['questionnaire_name'],))
            user_record = source_cursor.fetchone()
            
            if user_record:
                record_id = user_record['id']
                print(f"  用户记录ID: {record_id}")
                
                # 检查提交结果
                source_cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM crm_questionnaire_user_submit_result 
                    WHERE record_id = %s
                """, (record_id,))
                source_result_count = source_cursor.fetchone()['count']
                
                target_cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM crm_questionnaire_user_submit_result 
                    WHERE record_id = %s
                """, (record_id,))
                target_result_count = target_cursor.fetchone()['count']
                print(f"  提交结果数: 源库={source_result_count}, 目标库={target_result_count}")
                
                # 检查分析结果
                source_cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM crm_questionnaire_user_submit_result_analysis 
                    WHERE record_id = %s
                """, (record_id,))
                source_analysis_count = source_cursor.fetchone()['count']
                
                target_cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM crm_questionnaire_user_submit_result_analysis 
                    WHERE record_id = %s
                """, (record_id,))
                target_analysis_count = target_cursor.fetchone()['count']
                print(f"  分析结果数: 源库={source_analysis_count}, 目标库={target_analysis_count}")
        
        # 检查关联方式
        print("\n=== 检查关联方式 ===")
        # 检查 user_record 表结构
        source_cursor.execute("DESCRIBE crm_questionnaire_user_record")
        user_record_fields = [row['Field'] for row in source_cursor.fetchall()]
        print(f"crm_questionnaire_user_record 字段: {user_record_fields}")
        
        # 检查是否存在 template_id 或 questionnaire_id 字段
        has_template_id = 'template_id' in user_record_fields
        has_questionnaire_id = 'questionnaire_id' in user_record_fields
        has_questionnaire_name = 'questionnaire_name' in user_record_fields
        
        print(f"是否有 template_id 字段: {'是' if has_template_id else '否'}")
        print(f"是否有 questionnaire_id 字段: {'是' if has_questionnaire_id else '否'}")
        print(f"是否有 questionnaire_name 字段: {'是' if has_questionnaire_name else '否'}")
        
        if has_questionnaire_name:
            # 随机获取一条记录
            source_cursor.execute("SELECT questionnaire_name FROM crm_questionnaire_user_record LIMIT 1")
            user_record = source_cursor.fetchone()
            if user_record:
                questionnaire_name = user_record['questionnaire_name']
                # 查找对应的模板
                source_cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE questionnaire_name = %s LIMIT 1", (questionnaire_name,))
                template = source_cursor.fetchone()
                if template:
                    print(f"\n关联示例:")
                    print(f"  user_record.questionnaire_name: {questionnaire_name}")
                    print(f"  template.id: {template['id']}")
                    print(f"  template.questionnaire_name: {template['questionnaire_name']}")
                    print("\n结论: 通过 questionnaire_name 字段关联")
        
        print("\n=== 同步完成 ===")
        
    finally:
        # 关闭连接
        if source_cursor:
            source_cursor.close()
        if target_cursor:
            target_cursor.close()
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()

if __name__ == "__main__":
    main()
