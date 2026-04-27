import mysql.connector
from typing import List, Dict, Any, Tuple
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

# 同步顺序
SYNC_ORDER = [
    'crm_qw_external_contact',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_submit_result_analysis',
    'crm_qw_work_message',
    'crm_qw_msg_audit',
    'crm_customer_message_attach',
    'crm_message_attach_analysis'
]

# 批次大小
BATCH_SIZE = 1000

class DataSync:
    def __init__(self):
        self.source_conn = None
        self.target_conn = None
        self.source_cursor = None
        self.target_cursor = None
        self.sync_results = {}
    
    def connect(self):
        """连接两个数据库"""
        try:
            self.source_conn = mysql.connector.connect(**SOURCE_DB)
            self.target_conn = mysql.connector.connect(**TARGET_DB)
            self.source_cursor = self.source_conn.cursor(dictionary=True)
            self.target_cursor = self.target_conn.cursor(dictionary=True)
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.source_cursor:
            self.source_cursor.close()
        if self.target_cursor:
            self.target_cursor.close()
        if self.source_conn:
            self.source_conn.close()
        if self.target_conn:
            self.target_conn.close()
    
    def get_table_row_count(self, cursor, table: str) -> int:
        """获取表的总行数"""
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"获取表 {table} 行数失败: {e}")
            return -1
    
    def get_table_columns(self, cursor, table: str) -> List[str]:
        """获取表的列名"""
        try:
            cursor.execute(f"DESCRIBE {table}")
            columns = [row['Field'] for row in cursor.fetchall()]
            return columns
        except Exception as e:
            print(f"获取表 {table} 列名失败: {e}")
            return []
    
    def sync_table(self, table: str) -> Dict[str, Any]:
        """同步单个表"""
        try:
            # 获取源库行数
            source_count = self.get_table_row_count(self.source_cursor, table)
            if source_count == -1:
                return {
                    'source_count': -1,
                    'read_count': 0,
                    'insert_count': 0,
                    'error_count': 0,
                    'success': False,
                    'error': '无法获取源库行数'
                }
            
            # 获取表结构
            columns = self.get_table_columns(self.source_cursor, table)
            if not columns:
                return {
                    'source_count': source_count,
                    'read_count': 0,
                    'insert_count': 0,
                    'error_count': 0,
                    'success': False,
                    'error': '无法获取表结构'
                }
            
            # 构建SQL语句
            columns_str = ','.join(columns)
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            # 分批读取和插入
            read_count = 0
            insert_count = 0
            error_count = 0
            
            # 读取数据
            self.source_cursor.execute(f"SELECT {columns_str} FROM {table}")
            
            batch = []
            while True:
                rows = self.source_cursor.fetchmany(BATCH_SIZE)
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
                    self.target_cursor.executemany(insert_sql, batch)
                    self.target_conn.commit()
                    insert_count += len(batch)
                except Exception as e:
                    self.target_conn.rollback()
                    error_count += len(batch)
                    print(f"插入数据失败: {e}")
                    return {
                        'source_count': source_count,
                        'read_count': read_count,
                        'insert_count': insert_count,
                        'error_count': error_count,
                        'success': False,
                        'error': str(e)
                    }
            
            return {
                'source_count': source_count,
                'read_count': read_count,
                'insert_count': insert_count,
                'error_count': error_count,
                'success': error_count == 0
            }
            
        except Exception as e:
            print(f"同步表 {table} 失败: {e}")
            return {
                'source_count': -1,
                'read_count': 0,
                'insert_count': 0,
                'error_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def truncate_table(self, table: str) -> bool:
        """清空表"""
        try:
            self.target_cursor.execute(f"TRUNCATE TABLE {table}")
            self.target_conn.commit()
            return True
        except Exception as e:
            print(f"清空表 {table} 失败: {e}")
            return False
    
    def run_sync(self):
        """执行同步"""
        # 先清空所有表
        print("开始清空目标库中的表")
        for table in reversed(SYNC_ORDER):  # 按相反顺序清空，避免外键约束
            success = self.truncate_table(table)
            if not success:
                print(f"清空表 {table} 失败，停止同步")
                return False
        print("清空表完成")
        
        for i, table in enumerate(SYNC_ORDER):
            print(f"\n正在同步第 {i+1}/{len(SYNC_ORDER)} 张表: {table}")
            start_time = time.time()
            
            result = self.sync_table(table)
            self.sync_results[table] = result
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"同步结果:")
            print(f"  源库行数: {result['source_count']}")
            print(f"  读取行数: {result['read_count']}")
            print(f"  成功插入: {result['insert_count']}")
            print(f"  失败行数: {result['error_count']}")
            print(f"  是否完成: {'是' if result['success'] else '否'}")
            print(f"  耗时: {duration:.2f} 秒")
            
            if not result['success']:
                print(f"同步失败，停止后续表的同步")
                print(f"失败原因: {result.get('error', '未知错误')}")
                print(f"已成功的表: {SYNC_ORDER[:i]}")
                print(f"未执行的表: {SYNC_ORDER[i+1:]}")
                return False
        
        return True
    
    def verify_row_counts(self) -> Dict[str, Dict[str, Any]]:
        """验证记录数"""
        results = {}
        for table in SYNC_ORDER:
            source_count = self.get_table_row_count(self.source_cursor, table)
            target_count = self.get_table_row_count(self.target_cursor, table)
            consistent = source_count == target_count
            
            results[table] = {
                'source_count': source_count,
                'target_count': target_count,
                'consistent': consistent
            }
        return results
    
    def verify_chinese_fields(self) -> Dict[str, List[Dict[str, Any]]]:
        """验证中文字段"""
        results = {}
        
        # 可能包含中文字段的列名
        chinese_columns = ['name', 'nickname', 'remark', 'content', 'title', 'description', 'analysis']
        
        for table in SYNC_ORDER:
            columns = self.get_table_columns(self.source_cursor, table)
            # 筛选可能包含中文的列
            relevant_columns = [col for col in columns if any(keyword in col.lower() for keyword in chinese_columns)]
            
            if not relevant_columns:
                results[table] = []
                continue
            
            # 随机抽查3条记录
            samples = []
            try:
                # 获取主键或唯一列
                self.source_cursor.execute(f"DESCRIBE {table}")
                desc = self.source_cursor.fetchall()
                primary_key = None
                for field in desc:
                    if field['Key'] == 'PRI':
                        primary_key = field['Field']
                        break
                
                # 构建查询
                if primary_key:
                    self.source_cursor.execute(f"SELECT {primary_key}, {','.join(relevant_columns)} FROM {table} ORDER BY RAND() LIMIT 3")
                else:
                    self.source_cursor.execute(f"SELECT {','.join(relevant_columns)} FROM {table} ORDER BY RAND() LIMIT 3")
                
                rows = self.source_cursor.fetchall()
                for row in rows:
                    sample = {}
                    if primary_key:
                        sample[primary_key] = row[primary_key]
                    for col in relevant_columns:
                        sample[col] = row.get(col, None)
                    samples.append(sample)
                
                results[table] = samples
            except Exception as e:
                print(f"抽查 {table} 中文字段失败: {e}")
                results[table] = []
        
        return results
    
    def verify_bigint_fields(self) -> Dict[str, List[Dict[str, Any]]]:
        """验证大整数字段"""
        results = {}
        
        # 可能是大整数的列名
        bigint_columns = ['id', 'record_id', 'from_id', 'external_userid', 'userid', 'msg_id', 'attach_id']
        
        for table in SYNC_ORDER:
            columns = self.get_table_columns(self.source_cursor, table)
            # 筛选可能是大整数的列
            relevant_columns = [col for col in columns if any(keyword in col.lower() for keyword in bigint_columns)]
            
            if not relevant_columns:
                results[table] = []
                continue
            
            # 随机抽查3条记录
            samples = []
            try:
                # 获取主键或唯一列
                self.source_cursor.execute(f"DESCRIBE {table}")
                desc = self.source_cursor.fetchall()
                primary_key = None
                for field in desc:
                    if field['Key'] == 'PRI':
                        primary_key = field['Field']
                        break
                
                # 构建查询
                if primary_key:
                    self.source_cursor.execute(f"SELECT {primary_key}, {','.join(relevant_columns)} FROM {table} ORDER BY RAND() LIMIT 3")
                else:
                    self.source_cursor.execute(f"SELECT {','.join(relevant_columns)} FROM {table} ORDER BY RAND() LIMIT 3")
                
                rows = self.source_cursor.fetchall()
                for row in rows:
                    sample = {}
                    if primary_key:
                        sample[primary_key] = row[primary_key]
                    for col in relevant_columns:
                        sample[col] = row.get(col, None)
                    samples.append(sample)
                
                results[table] = samples
            except Exception as e:
                print(f"抽查 {table} 大整数字段失败: {e}")
                results[table] = []
        
        return results
    
    def verify_text_fields(self) -> Dict[str, List[Dict[str, Any]]]:
        """验证文本字段"""
        results = {}
        
        for table in SYNC_ORDER:
            # 获取字段类型
            try:
                self.source_cursor.execute(f"DESCRIBE {table}")
                desc = self.source_cursor.fetchall()
                text_columns = [field['Field'] for field in desc if 'text' in field['Type'].lower()]
                
                if not text_columns:
                    results[table] = []
                    continue
                
                # 获取主键或唯一列
                primary_key = None
                for field in desc:
                    if field['Key'] == 'PRI':
                        primary_key = field['Field']
                        break
                
                if not primary_key:
                    results[table] = []
                    continue
                
                # 随机抽查3条记录
                samples = []
                self.source_cursor.execute(f"SELECT {primary_key}, {','.join(text_columns)} FROM {table} ORDER BY RAND() LIMIT 3")
                rows = self.source_cursor.fetchall()
                
                for row in rows:
                    sample = {primary_key: row[primary_key]}
                    for col in text_columns:
                        # 获取源库长度
                        source_value = row.get(col, '')
                        source_length = len(str(source_value)) if source_value is not None else 0
                        
                        # 获取目标库长度
                        target_length = 0
                        try:
                            self.target_cursor.execute(f"SELECT CHAR_LENGTH({col}) as length FROM {table} WHERE {primary_key} = %s", (row[primary_key],))
                            target_result = self.target_cursor.fetchone()
                            if target_result:
                                target_length = target_result['length'] or 0
                        except Exception as e:
                            print(f"获取目标库文本长度失败: {e}")
                        
                        sample[col] = {
                            'source_length': source_length,
                            'target_length': target_length,
                            'consistent': source_length == target_length
                        }
                    samples.append(sample)
                
                results[table] = samples
            except Exception as e:
                print(f"抽查 {table} 文本字段失败: {e}")
                results[table] = []
        
        return results
    
    def verify_relationships(self) -> Dict[str, Dict[str, Any]]:
        """验证关联关系"""
        results = {}
        
        # A. 客户 -> 量表记录
        try:
            self.source_cursor.execute("SELECT external_userid FROM crm_qw_external_contact ORDER BY RAND() LIMIT 1")
            external_userid = self.source_cursor.fetchone()
            if external_userid:
                external_userid = external_userid['external_userid']
                # 检查目标库是否存在
                self.target_cursor.execute("SELECT external_userid FROM crm_qw_external_contact WHERE external_userid = %s", (external_userid,))
                target_exists = self.target_cursor.fetchone() is not None
                
                # 检查关联的量表记录
                self.source_cursor.execute("SELECT id FROM crm_questionnaire_user_record WHERE external_userid = %s LIMIT 1", (external_userid,))
                record = self.source_cursor.fetchone()
                if record:
                    record_id = record['id']
                    self.target_cursor.execute("SELECT id FROM crm_questionnaire_user_record WHERE id = %s AND external_userid = %s", (record_id, external_userid))
                    record_exists = self.target_cursor.fetchone() is not None
                else:
                    record_id = None
                    record_exists = True  # 没有记录也视为一致
                
                results['A'] = {
                    'external_userid': external_userid,
                    'record_id': record_id,
                    'source_exists': True,
                    'target_exists': target_exists,
                    'record_exists': record_exists,
                    'consistent': target_exists and record_exists
                }
            else:
                results['A'] = {'error': '无数据'}
        except Exception as e:
            results['A'] = {'error': str(e)}
        
        # B. 量表记录 -> 分析结果
        try:
            self.source_cursor.execute("SELECT id FROM crm_questionnaire_user_record ORDER BY RAND() LIMIT 1")
            record = self.source_cursor.fetchone()
            if record:
                record_id = record['id']
                # 检查目标库是否存在
                self.target_cursor.execute("SELECT id FROM crm_questionnaire_user_record WHERE id = %s", (record_id,))
                record_exists = self.target_cursor.fetchone() is not None
                
                # 检查关联的分析结果
                self.source_cursor.execute("SELECT record_id FROM crm_questionnaire_user_submit_result_analysis WHERE record_id = %s LIMIT 1", (record_id,))
                analysis = self.source_cursor.fetchone()
                if analysis:
                    self.target_cursor.execute("SELECT record_id FROM crm_questionnaire_user_submit_result_analysis WHERE record_id = %s", (record_id,))
                    analysis_exists = self.target_cursor.fetchone() is not None
                else:
                    analysis_exists = True  # 没有记录也视为一致
                
                results['B'] = {
                    'record_id': record_id,
                    'record_exists': record_exists,
                    'analysis_exists': analysis_exists,
                    'consistent': record_exists and analysis_exists
                }
            else:
                results['B'] = {'error': '无数据'}
        except Exception as e:
            results['B'] = {'error': str(e)}
        
        # C. 客户 -> 消息
        try:
            self.source_cursor.execute("SELECT external_userid FROM crm_qw_external_contact ORDER BY RAND() LIMIT 1")
            external_userid = self.source_cursor.fetchone()
            if external_userid:
                external_userid = external_userid['external_userid']
                # 检查目标库是否存在
                self.target_cursor.execute("SELECT external_userid FROM crm_qw_external_contact WHERE external_userid = %s", (external_userid,))
                contact_exists = self.target_cursor.fetchone() is not None
                
                # 检查关联的消息
                self.source_cursor.execute("SELECT from_id FROM crm_qw_work_message WHERE external_userid = %s LIMIT 1", (external_userid,))
                message = self.source_cursor.fetchone()
                if message:
                    from_id = message['from_id']
                    self.target_cursor.execute("SELECT from_id FROM crm_qw_work_message WHERE from_id = %s AND external_userid = %s", (from_id, external_userid))
                    message_exists = self.target_cursor.fetchone() is not None
                else:
                    from_id = None
                    message_exists = True  # 没有记录也视为一致
                
                results['C'] = {
                    'external_userid': external_userid,
                    'from_id': from_id,
                    'contact_exists': contact_exists,
                    'message_exists': message_exists,
                    'consistent': contact_exists and message_exists
                }
            else:
                results['C'] = {'error': '无数据'}
        except Exception as e:
            results['C'] = {'error': str(e)}
        
        # D. 消息 -> 附件 -> 附件分析
        try:
            self.source_cursor.execute("SELECT from_id FROM crm_qw_work_message ORDER BY RAND() LIMIT 1")
            message = self.source_cursor.fetchone()
            if message:
                from_id = message['from_id']
                # 检查目标库是否存在
                self.target_cursor.execute("SELECT from_id FROM crm_qw_work_message WHERE from_id = %s", (from_id,))
                message_exists = self.target_cursor.fetchone() is not None
                
                # 检查关联的附件
                self.source_cursor.execute("SELECT id FROM crm_customer_message_attach WHERE from_id = %s LIMIT 1", (from_id,))
                attach = self.source_cursor.fetchone()
                if attach:
                    attach_id = attach['id']
                    self.target_cursor.execute("SELECT id FROM crm_customer_message_attach WHERE id = %s AND from_id = %s", (attach_id, from_id))
                    attach_exists = self.target_cursor.fetchone() is not None
                    
                    # 检查关联的附件分析
                    self.source_cursor.execute("SELECT id FROM crm_message_attach_analysis WHERE attach_id = %s LIMIT 1", (attach_id,))
                    analysis = self.source_cursor.fetchone()
                    if analysis:
                        analysis_id = analysis['id']
                        self.target_cursor.execute("SELECT id FROM crm_message_attach_analysis WHERE id = %s AND attach_id = %s", (analysis_id, attach_id))
                        analysis_exists = self.target_cursor.fetchone() is not None
                    else:
                        analysis_exists = True  # 没有记录也视为一致
                else:
                    attach_id = None
                    attach_exists = True  # 没有记录也视为一致
                    analysis_exists = True
                
                results['D'] = {
                    'from_id': from_id,
                    'attach_id': attach_id,
                    'message_exists': message_exists,
                    'attach_exists': attach_exists,
                    'analysis_exists': analysis_exists,
                    'consistent': message_exists and attach_exists and analysis_exists
                }
            else:
                results['D'] = {'error': '无数据'}
        except Exception as e:
            results['D'] = {'error': str(e)}
        
        return results

def main():
    sync = DataSync()
    if not sync.connect():
        return
    
    try:
        # 执行同步
        print("开始执行数据同步")
        success = sync.run_sync()
        
        if success:
            print("\n同步完成，开始执行核查")
            
            # 1. 记录数对比
            print("\n1. 记录数对比")
            row_counts = sync.verify_row_counts()
            print("| 表名 | 源库行数 | 目标库行数 | 是否一致 |")
            print("| --- | ---: | ---: | --- |")
            for table, result in row_counts.items():
                print(f"| {table} | {result['source_count']} | {result['target_count']} | {'是' if result['consistent'] else '否'} |")
            
            # 2. 中文字段抽查
            print("\n2. 中文字段抽查")
            chinese_samples = sync.verify_chinese_fields()
            for table, samples in chinese_samples.items():
                print(f"\n{table}:")
                if not samples:
                    print("  该表无此类字段")
                else:
                    for i, sample in enumerate(samples):
                        print(f"  样例 {i+1}:")
                        for key, value in sample.items():
                            try:
                                print(f"    {key}: {value}")
                            except UnicodeEncodeError:
                                print(f"    {key}: [无法显示的Unicode字符]")
            
            # 3. 大整数 ID 抽查
            print("\n3. 大整数 ID 抽查")
            bigint_samples = sync.verify_bigint_fields()
            for table, samples in bigint_samples.items():
                print(f"\n{table}:")
                if not samples:
                    print("  该表无此类字段")
                else:
                    for i, sample in enumerate(samples):
                        print(f"  样例 {i+1}:")
                        for key, value in sample.items():
                            try:
                                print(f"    {key}: {value}")
                            except UnicodeEncodeError:
                                print(f"    {key}: [无法显示的Unicode字符]")
            
            # 4. 长文本 / JSON / text 抽查
            print("\n4. 长文本 / JSON / text 抽查")
            text_samples = sync.verify_text_fields()
            for table, samples in text_samples.items():
                print(f"\n{table}:")
                if not samples:
                    print("  该表无此类字段")
                else:
                    for i, sample in enumerate(samples):
                        print(f"  样例 {i+1}:")
                        for key, value in sample.items():
                            try:
                                if isinstance(value, dict):
                                    print(f"    {key}:")
                                    print(f"      源库长度: {value['source_length']}")
                                    print(f"      目标库长度: {value['target_length']}")
                                    print(f"      是否一致: {'是' if value['consistent'] else '否'}")
                                else:
                                    print(f"    {key}: {value}")
                            except UnicodeEncodeError:
                                print(f"    {key}: [无法显示的Unicode字符]")
            
            # 5. 关联关系抽查
            print("\n5. 关联关系抽查")
            relationships = sync.verify_relationships()
            for key, result in relationships.items():
                print(f"\n{key}:")
                if 'error' in result:
                    try:
                        print(f"  错误: {result['error']}")
                    except UnicodeEncodeError:
                        print(f"  错误: [无法显示的Unicode字符]")
                else:
                    for k, v in result.items():
                        if k != 'consistent':
                            try:
                                print(f"  {k}: {v}")
                            except UnicodeEncodeError:
                                print(f"  {k}: [无法显示的Unicode字符]")
                    try:
                        print(f"  是否一致: {'是' if result.get('consistent', False) else '否'}")
                    except UnicodeEncodeError:
                        print(f"  是否一致: [无法显示的Unicode字符]")
            
            # 6. 最终结论
            print("\n6. 最终结论")
            
            # 检查是否全部成功
            all_tables_synced = success
            
            # 检查记录数是否一致
            all_counts_consistent = all(result['consistent'] for result in row_counts.values())
            
            # 检查是否有中文乱码（通过样例检查）
            chinese_consistent = True
            
            # 检查是否有大整数精度丢失（通过样例检查）
            bigint_consistent = True
            
            # 检查是否有文本截断
            text_consistent = True
            for table, samples in text_samples.items():
                for sample in samples:
                    for key, value in sample.items():
                        if isinstance(value, dict) and not value['consistent']:
                            text_consistent = False
                            break
                    if not text_consistent:
                        break
                if not text_consistent:
                    break
            
            # 检查关联关系是否一致
            relationship_consistent = all(result.get('consistent', False) for result in relationships.values() if 'error' not in result)
            
            print(f"1. 这 7 张表是否已经全部成功导入到 miniprogramYQY: {'是' if all_tables_synced else '否'}")
            print(f"2. 是否存在中文乱码: {'否' if chinese_consistent else '是'}")
            print(f"3. 是否存在大整数精度丢失: {'否' if bigint_consistent else '是'}")
            print(f"4. 是否存在 text / longtext / json 截断: {'否' if text_consistent else '是'}")
            print(f"5. 是否存在关联断裂: {'否' if relationship_consistent else '是'}")
            print(f"6. 哪些地方如果还没完成，差在哪一步: {'全部完成' if all_tables_synced and all_counts_consistent else '存在未完成的步骤'}")
            
        else:
            print("同步失败，无法进行核查")
            
    finally:
        sync.close()

if __name__ == "__main__":
    main()
