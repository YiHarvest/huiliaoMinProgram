import mysql.connector
from typing import List, Dict, Any
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

class QuestionnaireSync:
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
    
    def get_create_table_statement(self, cursor, table: str) -> str:
        """获取表的创建语句"""
        try:
            cursor.execute(f"SHOW CREATE TABLE {table}")
            result = cursor.fetchone()
            return result['Create Table'] if result else None
        except Exception as e:
            print(f"获取表 {table} 创建语句失败: {e}")
            return None
    
    def create_table(self, cursor, create_statement: str) -> bool:
        """创建表"""
        try:
            cursor.execute(create_statement)
            return True
        except Exception as e:
            print(f"创建表失败: {e}")
            return False
    
    def check_tables_exist(self) -> Dict[str, Dict[str, bool]]:
        """检查表是否存在"""
        results = {}
        for table in TABLES_TO_SYNC:
            results[table] = {
                'source_exists': self._check_table_exists(self.source_cursor, table),
                'target_exists': self._check_table_exists(self.target_cursor, table)
            }
        return results
    
    def _check_table_exists(self, cursor, table: str) -> bool:
        """检查单个表是否存在"""
        try:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"检查表 {table} 失败: {e}")
            return False
    
    def create_missing_tables(self) -> bool:
        """创建缺失的表"""
        table_exists = self.check_tables_exist()
        
        print("\n检查表存在情况:")
        for table, exists in table_exists.items():
            print(f"{table}: 源库={'存在' if exists['source_exists'] else '不存在'}, 目标库={'存在' if exists['target_exists'] else '不存在'}")
        
        # 创建缺失的表
        for table in TABLES_TO_SYNC:
            if not table_exists[table]['target_exists']:
                print(f"\n创建表 {table}")
                create_stmt = self.get_create_table_statement(self.source_cursor, table)
                if create_stmt:
                    success = self.create_table(self.target_cursor, create_stmt)
                    if not success:
                        print(f"创建表 {table} 失败")
                        return False
                else:
                    print(f"无法获取表 {table} 的创建语句")
                    return False
        
        # 提交事务
        if self.target_conn:
            self.target_conn.commit()
        
        return True
    
    def compare_table_structures(self) -> bool:
        """对比表结构"""
        print("\n对比表结构:")
        all_consistent = True
        
        for table in TABLES_TO_SYNC:
            source_create = self.get_create_table_statement(self.source_cursor, table)
            target_create = self.get_create_table_statement(self.target_cursor, table)
            
            if source_create and target_create:
                # 简单比较创建语句
                consistent = source_create == target_create
                all_consistent &= consistent
                print(f"{table}: {'一致' if consistent else '不一致'}")
                if not consistent:
                    print("  源库创建语句:", source_create[:500], "...")
                    print("  目标库创建语句:", target_create[:500], "...")
            else:
                all_consistent = False
                print(f"{table}: 无法获取创建语句")
        
        return all_consistent
    
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
    
    def truncate_table(self, table: str) -> bool:
        """清空表"""
        try:
            self.target_cursor.execute(f"TRUNCATE TABLE {table}")
            self.target_conn.commit()
            return True
        except Exception as e:
            print(f"清空表 {table} 失败: {e}")
            return False
    
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
    
    def run_sync(self):
        """执行同步"""
        # 先清空所有表
        print("开始清空目标库中的表")
        for table in reversed(TABLES_TO_SYNC):  # 按相反顺序清空，避免外键约束
            success = self.truncate_table(table)
            if not success:
                print(f"清空表 {table} 失败，停止同步")
                return False
        print("清空表完成")
        
        for i, table in enumerate(TABLES_TO_SYNC):
            print(f"\n正在同步第 {i+1}/{len(TABLES_TO_SYNC)} 张表: {table}")
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
                print(f"已成功的表: {TABLES_TO_SYNC[:i]}")
                print(f"未执行的表: {TABLES_TO_SYNC[i+1:]}")
                return False
        
        return True
    
    def verify_row_counts(self):
        """验证记录数"""
        results = {}
        for table in TABLES_TO_SYNC:
            source_count = self.get_table_row_count(self.source_cursor, table)
            target_count = self.get_table_row_count(self.target_cursor, table)
            consistent = source_count == target_count
            
            results[table] = {
                'source_count': source_count,
                'target_count': target_count,
                'consistent': consistent
            }
        return results
    
    def verify_json_fields(self):
        """验证 JSON 字段"""
        results = {}
        
        # 检查包含 JSON 字段的表
        json_tables = {
            'crm_subject': 'subject_content'
        }
        
        for table, json_field in json_tables.items():
            samples = []
            try:
                # 随机抽查3条记录
                self.source_cursor.execute(f"SELECT id, {json_field} FROM {table} ORDER BY RAND() LIMIT 3")
                source_rows = self.source_cursor.fetchall()
                
                for row in source_rows:
                    source_value = row[json_field]
                    source_length = len(str(source_value)) if source_value is not None else 0
                    
                    # 在目标库中查找对应记录
                    self.target_cursor.execute(f"SELECT {json_field} FROM {table} WHERE id = %s", (row['id'],))
                    target_row = self.target_cursor.fetchone()
                    target_value = target_row[json_field] if target_row else None
                    target_length = len(str(target_value)) if target_value is not None else 0
                    
                    samples.append({
                        'id': row['id'],
                        'source_length': source_length,
                        'target_length': target_length,
                        'consistent': source_length == target_length,
                        'source_value': source_value[:200] + '...' if source_value and len(str(source_value)) > 200 else source_value,
                        'target_value': target_value[:200] + '...' if target_value and len(str(target_value)) > 200 else target_value
                    })
                
                results[table] = samples
            except Exception as e:
                print(f"验证 {table} 的 JSON 字段失败: {e}")
                results[table] = []
        
        return results
    
    def verify_multiple_submissions(self):
        """验证多次填写"""
        samples = []
        try:
            # 查找有多次填写记录的用户
            self.source_cursor.execute("""
                SELECT external_user_id, questionnaire_name, COUNT(*) as submit_count 
                FROM crm_questionnaire_user_record 
                GROUP BY external_user_id, questionnaire_name 
                HAVING COUNT(*) > 1 
                LIMIT 3
            """)
            users = self.source_cursor.fetchall()
            
            for user in users:
                # 获取该用户的所有填写记录
                self.source_cursor.execute("""
                    SELECT id, create_time 
                    FROM crm_questionnaire_user_record 
                    WHERE external_user_id = %s AND questionnaire_name = %s 
                    ORDER BY create_time
                """, (user['external_user_id'], user['questionnaire_name']))
                source_records = self.source_cursor.fetchall()
                
                # 检查目标库中是否存在这些记录
                target_records = []
                for record in source_records:
                    self.target_cursor.execute("""
                        SELECT id, create_time 
                        FROM crm_questionnaire_user_record 
                        WHERE id = %s
                    "", (record['id'],))
                    target_record = self.target_cursor.fetchone()
                    if target_record:
                        target_records.append(target_record)
                
                samples.append({
                    'external_user_id': user['external_user_id'],
                    'questionnaire_name': user['questionnaire_name'],
                    'submit_count': user['submit_count'],
                    'source_records': len(source_records),
                    'target_records': len(target_records),
                    'consistent': len(source_records) == len(target_records)
                })
        except Exception as e:
            print(f"验证多次填写失败: {e}")
        
        return samples
    
    def verify_full_link(self):
        """验证完整链路"""
        try:
            # 随机获取一个模板
            self.source_cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template ORDER BY RAND() LIMIT 1")
            template = self.source_cursor.fetchone()
            if not template:
                return {'error': '未找到模板'}
            
            template_id = template['id']
            
            # 获取模板的题目
            self.source_cursor.execute("""
                SELECT t.id, t.template_id, t.subject_id, s.subject_title 
                FROM crm_questionnaire_template_subject t 
                JOIN crm_subject s ON t.subject_id = s.id 
                WHERE t.template_id = %s 
                LIMIT 3
            """, (template_id,))
            template_subjects = self.source_cursor.fetchall()
            
            # 获取用户记录
            self.source_cursor.execute("""
                SELECT id, external_user_id, questionnaire_name 
                FROM crm_questionnaire_user_record 
                WHERE questionnaire_name = %s 
                LIMIT 1
            """, (template['questionnaire_name'],))
            user_record = self.source_cursor.fetchone()
            
            if not user_record:
                return {'error': '未找到用户记录'}
            
            record_id = user_record['id']
            
            # 获取提交结果
            self.source_cursor.execute("""
                SELECT id, record_id, subject_id, answer 
                FROM crm_questionnaire_user_submit_result 
                WHERE record_id = %s 
                LIMIT 3
            """, (record_id,))
            submit_results = self.source_cursor.fetchall()
            
            # 获取分析结果
            self.source_cursor.execute("""
                SELECT id, record_id, analysis_result 
                FROM crm_questionnaire_user_submit_result_analysis 
                WHERE record_id = %s 
                LIMIT 1
            """, (record_id,))
            analysis = self.source_cursor.fetchone()
            
            # 检查目标库中是否存在这些记录
            target_template_exists = False
            self.target_cursor.execute("SELECT id FROM crm_questionnaire_template WHERE id = %s", (template_id,))
            if self.target_cursor.fetchone():
                target_template_exists = True
            
            target_subjects_count = 0
            self.target_cursor.execute("SELECT COUNT(*) as count FROM crm_questionnaire_template_subject WHERE template_id = %s", (template_id,))
            count_result = self.target_cursor.fetchone()
            if count_result:
                target_subjects_count = count_result['count']
            
            target_record_exists = False
            self.target_cursor.execute("SELECT id FROM crm_questionnaire_user_record WHERE id = %s", (record_id,))
            if self.target_cursor.fetchone():
                target_record_exists = True
            
            target_results_count = 0
            self.target_cursor.execute("SELECT COUNT(*) as count FROM crm_questionnaire_user_submit_result WHERE record_id = %s", (record_id,))
            count_result = self.target_cursor.fetchone()
            if count_result:
                target_results_count = count_result['count']
            
            target_analysis_exists = False
            self.target_cursor.execute("SELECT id FROM crm_questionnaire_user_submit_result_analysis WHERE record_id = %s", (record_id,))
            if self.target_cursor.fetchone():
                target_analysis_exists = True
            
            return {
                'template': template,
                'template_subjects_count': len(template_subjects),
                'user_record': user_record,
                'submit_results_count': len(submit_results),
                'analysis_exists': analysis is not None,
                'target_template_exists': target_template_exists,
                'target_subjects_count': target_subjects_count,
                'target_record_exists': target_record_exists,
                'target_results_count': target_results_count,
                'target_analysis_exists': target_analysis_exists,
                'consistent': all([
                    target_template_exists,
                    target_subjects_count == len(template_subjects),
                    target_record_exists,
                    target_results_count == len(submit_results),
                    target_analysis_exists == (analysis is not None)
                ])
            }
        except Exception as e:
            print(f"验证完整链路失败: {e}")
            return {'error': str(e)}
    
    def check_record_template_relationship(self):
        """检查用户记录与模板的关联方式"""
        print("\n检查 crm_questionnaire_user_record 与 crm_questionnaire_template 的关联方式:")
        
        # 检查 user_record 表结构
        self.source_cursor.execute("DESCRIBE crm_questionnaire_user_record")
        user_record_fields = [row['Field'] for row in self.source_cursor.fetchall()]
        print(f"crm_questionnaire_user_record 字段: {user_record_fields}")
        
        # 检查是否存在 template_id 或 questionnaire_id 字段
        has_template_id = 'template_id' in user_record_fields
        has_questionnaire_id = 'questionnaire_id' in user_record_fields
        has_questionnaire_name = 'questionnaire_name' in user_record_fields
        
        print(f"是否有 template_id 字段: {'是' if has_template_id else '否'}")
        print(f"是否有 questionnaire_id 字段: {'是' if has_questionnaire_id else '否'}")
        print(f"是否有 questionnaire_name 字段: {'是' if has_questionnaire_name else '否'}")
        
        # 检查实际关联方式
        if has_questionnaire_name:
            # 随机获取一条记录
            self.source_cursor.execute("SELECT questionnaire_name FROM crm_questionnaire_user_record LIMIT 1")
            user_record = self.source_cursor.fetchone()
            if user_record:
                questionnaire_name = user_record['questionnaire_name']
                # 查找对应的模板
                self.source_cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE questionnaire_name = %s LIMIT 1", (questionnaire_name,))
                template = self.source_cursor.fetchone()
                if template:
                    print(f"\n关联示例:")
                    print(f"  user_record.questionnaire_name: {questionnaire_name}")
                    print(f"  template.id: {template['id']}")
                    print(f"  template.questionnaire_name: {template['questionnaire_name']}")
                    print("\n结论: 通过 questionnaire_name 字段关联")
                else:
                    print("\n未找到对应模板，无法确认关联方式")
            else:
                print("\n未找到用户记录，无法确认关联方式")
        else:
            print("\n未找到有效的关联字段")

def main():
    sync = QuestionnaireSync()
    if not sync.connect():
        return
    
    try:
        # 检查并创建表
        print("=== 检查并创建表 ===")
        if not sync.create_missing_tables():
            print("创建表失败，停止同步")
            return
        
        # 对比表结构
        print("\n=== 对比表结构 ===")
        if not sync.compare_table_structures():
            print("表结构不一致，停止同步")
            return
        
        # 执行同步
        print("\n=== 执行数据同步 ===")
        if not sync.run_sync():
            print("同步失败")
            return
        
        # 验证记录数
        print("\n=== 验证记录数 ===")
        row_counts = sync.verify_row_counts()
        print("| 表名 | 源库行数 | 目标库行数 | 是否一致 |")
        print("| --- | ---: | ---: | --- |")
        for table, result in row_counts.items():
            print(f"| {table} | {result['source_count']} | {result['target_count']} | {'是' if result['consistent'] else '否'} |")
        
        # 验证 JSON 字段
        print("\n=== 验证 JSON 字段 ===")
        json_samples = sync.verify_json_fields()
        for table, samples in json_samples.items():
            print(f"\n{table}:")
            for i, sample in enumerate(samples):
                print(f"  样例 {i+1}:")
                print(f"    ID: {sample['id']}")
                print(f"    源库长度: {sample['source_length']}")
                print(f"    目标库长度: {sample['target_length']}")
                print(f"    是否一致: {'是' if sample['consistent'] else '否'}")
                print(f"    源库内容: {sample['source_value']}")
                print(f"    目标库内容: {sample['target_value']}")
        
        # 验证多次填写
        print("\n=== 验证多次填写 ===")
        multiple_samples = sync.verify_multiple_submissions()
        for i, sample in enumerate(multiple_samples):
            print(f"  样例 {i+1}:")
            print(f"    用户: {sample['external_user_id']}")
            print(f"    量表: {sample['questionnaire_name']}")
            print(f"    填写次数: {sample['submit_count']}")
            print(f"    源库记录数: {sample['source_records']}")
            print(f"    目标库记录数: {sample['target_records']}")
            print(f"    是否一致: {'是' if sample['consistent'] else '否'}")
        
        # 验证完整链路
        print("\n=== 验证完整链路 ===")
        full_link = sync.verify_full_link()
        if 'error' in full_link:
            print(f"  错误: {full_link['error']}")
        else:
            print(f"  模板: {full_link['template']['questionnaire_name']} (ID: {full_link['template']['id']})")
            print(f"  模板题目数: {full_link['template_subjects_count']}")
            print(f"  用户记录: {full_link['user_record']['external_user_id']} (ID: {full_link['user_record']['id']})")
            print(f"  提交结果数: {full_link['submit_results_count']}")
            print(f"  分析结果: {'存在' if full_link['analysis_exists'] else '不存在'}")
            print(f"  目标库模板: {'存在' if full_link['target_template_exists'] else '不存在'}")
            print(f"  目标库题目数: {full_link['target_subjects_count']}")
            print(f"  目标库用户记录: {'存在' if full_link['target_record_exists'] else '不存在'}")
            print(f"  目标库提交结果数: {full_link['target_results_count']}")
            print(f"  目标库分析结果: {'存在' if full_link['target_analysis_exists'] else '不存在'}")
            print(f"  链路是否一致: {'是' if full_link['consistent'] else '否'}")
        
        # 检查关联方式
        sync.check_record_template_relationship()
        
        print("\n=== 同步完成 ===")
        
    finally:
        sync.close()

if __name__ == "__main__":
    main()
