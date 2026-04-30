import mysql.connector
import json
import hashlib
import random

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

# 需要核验的表
TABLES_TO_VERIFY = [
    'crm_questionnaire_template',
    'crm_questionnaire_template_subject',
    'crm_subject',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

class ConsistencyVerifier:
    def __init__(self):
        self.source_conn = None
        self.target_conn = None
        self.source_cursor = None
        self.target_cursor = None
    
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
    
    def get_table_structure(self, cursor, table: str) -> list:
        """获取表结构"""
        try:
            cursor.execute(f"DESCRIBE {table}")
            return cursor.fetchall()
        except Exception as e:
            print(f"获取表 {table} 结构失败: {e}")
            return []
    
    def get_indexes(self, cursor, table: str) -> list:
        """获取表的索引"""
        try:
            cursor.execute(f"SHOW INDEX FROM {table}")
            return cursor.fetchall()
        except Exception as e:
            print(f"获取表 {table} 索引失败: {e}")
            return []
    
    def get_row_count(self, cursor, table: str) -> int:
        """获取表的行数"""
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"获取表 {table} 行数失败: {e}")
            return -1
    
    def get_distinct_count(self, cursor, table: str, primary_key: str) -> int:
        """获取主键的 distinct 数量"""
        try:
            cursor.execute(f"SELECT COUNT(DISTINCT {primary_key}) as count FROM {table}")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"获取表 {table} 主键 distinct 数量失败: {e}")
            return -1
    
    def get_sample_records(self, cursor, table: str, limit: int) -> list:
        """获取表的样本记录"""
        try:
            # 先获取主键
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            primary_key = None
            for col in columns:
                if col['Key'] == 'PRI':
                    primary_key = col['Field']
                    break
            
            if primary_key:
                # 按主键排序获取前N条
                cursor.execute(f"SELECT * FROM {table} ORDER BY {primary_key} LIMIT {limit}")
            else:
                # 随机获取
                cursor.execute(f"SELECT * FROM {table} ORDER BY RAND() LIMIT {limit}")
            
            return cursor.fetchall()
        except Exception as e:
            print(f"获取表 {table} 样本记录失败: {e}")
            return []
    
    def compare_records(self, source_record, target_record) -> dict:
        """比较两条记录是否一致"""
        if not source_record or not target_record:
            return {'consistent': False, 'differences': ['记录不存在']}
        
        differences = []
        all_fields = set(source_record.keys()) | set(target_record.keys())
        
        for field in all_fields:
            source_value = source_record.get(field)
            target_value = target_record.get(field)
            
            # 处理NULL值
            if source_value is None and target_value is None:
                continue
            if source_value is None or target_value is None:
                differences.append(f"{field}: 源库={source_value}, 目标库={target_value}")
                continue
            
            # 处理时间类型
            if isinstance(source_value, str) and isinstance(target_value, str):
                # 去除毫秒部分进行比较
                if ' ' in source_value and ' ' in target_value:
                    source_value = source_value.split('.')[0]
                    target_value = target_value.split('.')[0]
            
            if source_value != target_value:
                differences.append(f"{field}: 源库={source_value}, 目标库={target_value}")
        
        return {'consistent': len(differences) == 0, 'differences': differences}
    
    def verify_structure_consistency(self) -> dict:
        """验证结构一致性"""
        results = {}
        
        for table in TABLES_TO_VERIFY:
            # 获取创建语句
            source_create = self.get_create_table_statement(self.source_cursor, table)
            target_create = self.get_create_table_statement(self.target_cursor, table)
            
            # 获取表结构
            source_structure = self.get_table_structure(self.source_cursor, table)
            target_structure = self.get_table_structure(self.target_cursor, table)
            
            # 获取索引
            source_indexes = self.get_indexes(self.source_cursor, table)
            target_indexes = self.get_indexes(self.target_cursor, table)
            
            # 比较字段
            fields_consistent = len(source_structure) == len(target_structure)
            if fields_consistent:
                for i, (source_field, target_field) in enumerate(zip(source_structure, target_structure)):
                    if source_field != target_field:
                        fields_consistent = False
                        break
            
            # 比较索引
            indexes_consistent = len(source_indexes) == len(target_indexes)
            if indexes_consistent:
                # 简化比较，只比较索引名称和类型
                source_index_names = [f"{idx['Key_name']}:{idx['Seq_in_index']}" for idx in source_indexes]
                target_index_names = [f"{idx['Key_name']}:{idx['Seq_in_index']}" for idx in target_indexes]
                indexes_consistent = sorted(source_index_names) == sorted(target_index_names)
            
            # 比较创建语句（粗略判断字符集和存储引擎）
            create_consistent = source_create == target_create
            charset_consistent = True
            if source_create and target_create:
                # 检查字符集和排序规则
                source_charset = self._extract_charset(source_create)
                target_charset = self._extract_charset(target_create)
                charset_consistent = source_charset == target_charset
            
            results[table] = {
                'create_consistent': create_consistent,
                'fields_consistent': fields_consistent,
                'indexes_consistent': indexes_consistent,
                'charset_consistent': charset_consistent,
                'passed': create_consistent and fields_consistent and indexes_consistent and charset_consistent
            }
        
        return results
    
    def _extract_charset(self, create_statement: str) -> str:
        """从创建语句中提取字符集和排序规则"""
        import re
        charset_match = re.search(r'CHARACTER SET\s+([^\s]+)', create_statement)
        collation_match = re.search(r'COLLATE\s+([^\s]+)', create_statement)
        
        charset = charset_match.group(1) if charset_match else ''
        collation = collation_match.group(1) if collation_match else ''
        return f"{charset}:{collation}"
    
    def verify_basic_data_consistency(self) -> dict:
        """验证基础数据一致性"""
        results = {}
        
        for table in TABLES_TO_VERIFY:
            # 获取主键
            cursor = self.source_cursor
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            primary_key = None
            for col in columns:
                if col['Key'] == 'PRI':
                    primary_key = col['Field']
                    break
            
            if not primary_key:
                results[table] = {
                    'source_count': -1,
                    'target_count': -1,
                    'source_distinct': -1,
                    'target_distinct': -1,
                    'consistent': False
                }
                continue
            
            # 获取行数
            source_count = self.get_row_count(self.source_cursor, table)
            target_count = self.get_row_count(self.target_cursor, table)
            
            # 获取distinct主键数量
            source_distinct = self.get_distinct_count(self.source_cursor, table, primary_key)
            target_distinct = self.get_distinct_count(self.target_cursor, table, primary_key)
            
            consistent = source_count == target_count and source_distinct == target_distinct
            
            results[table] = {
                'source_count': source_count,
                'target_count': target_count,
                'source_distinct': source_distinct,
                'target_distinct': target_distinct,
                'consistent': consistent
            }
        
        return results
    
    def verify_sample_records(self, sample_size: int = 20) -> dict:
        """验证抽样记录"""
        results = {}
        
        for table in TABLES_TO_VERIFY:
            # 获取源库样本
            source_samples = self.get_sample_records(self.source_cursor, table, sample_size)
            
            # 获取主键
            cursor = self.source_cursor
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            primary_key = None
            for col in columns:
                if col['Key'] == 'PRI':
                    primary_key = col['Field']
                    break
            
            if not primary_key:
                results[table] = {'samples': [], 'consistent_count': 0, 'total_count': 0}
                continue
            
            sample_results = []
            for source_record in source_samples:
                pk_value = source_record[primary_key]
                
                # 在目标库中查找对应记录
                self.target_cursor.execute(f"SELECT * FROM {table} WHERE {primary_key} = %s", (pk_value,))
                target_record = self.target_cursor.fetchone()
                
                # 比较记录
                comparison = self.compare_records(source_record, target_record)
                sample_results.append({
                    'primary_key': pk_value,
                    'consistent': comparison['consistent'],
                    'differences': comparison['differences']
                })
            
            consistent_count = sum(1 for r in sample_results if r['consistent'])
            results[table] = {
                'samples': sample_results,
                'consistent_count': consistent_count,
                'total_count': len(sample_results),
                'consistent_rate': consistent_count / len(sample_results) if sample_results else 0
            }
        
        return results
    
    def verify_json_fields(self) -> dict:
        """验证JSON字段"""
        results = {}
        
        # 检查 crm_subject.subject_content
        table = 'crm_subject'
        field = 'subject_content'
        
        # 获取样本
        self.source_cursor.execute(f"SELECT id, {field} FROM {table} ORDER BY RAND() LIMIT 20")
        source_samples = self.source_cursor.fetchall()
        
        sample_results = []
        for source_record in source_samples:
            pk_value = source_record['id']
            source_value = source_record[field]
            source_length = len(str(source_value)) if source_value else 0
            
            # 尝试解析JSON
            json_valid = True
            try:
                if source_value:
                    json.loads(source_value)
            except:
                json_valid = False
            
            # 在目标库中查找对应记录
            self.target_cursor.execute(f"SELECT {field} FROM {table} WHERE id = %s", (pk_value,))
            target_record = self.target_cursor.fetchone()
            
            if target_record:
                target_value = target_record[field]
                target_length = len(str(target_value)) if target_value else 0
                
                # 尝试解析JSON
                target_json_valid = True
                try:
                    if target_value:
                        json.loads(target_value)
                except:
                    target_json_valid = False
                
                consistent = source_length == target_length and json_valid == target_json_valid
                if source_value and target_value:
                    consistent = consistent and source_value == target_value
            else:
                target_value = None
                target_length = 0
                target_json_valid = False
                consistent = False
            
            sample_results.append({
                'id': pk_value,
                'source_length': source_length,
                'target_length': target_length,
                'source_json_valid': json_valid,
                'target_json_valid': target_json_valid,
                'consistent': consistent,
                'source_sample': source_value[:100] + '...' if source_value and len(str(source_value)) > 100 else source_value,
                'target_sample': target_value[:100] + '...' if target_value and len(str(target_value)) > 100 else target_value
            })
        
        results[table] = {
            'samples': sample_results,
            'consistent_count': sum(1 for r in sample_results if r['consistent']),
            'total_count': len(sample_results)
        }
        
        return results
    
    def verify_chinese_fields(self) -> dict:
        """验证中文字段"""
        results = {}
        
        # 可能包含中文的字段
        chinese_fields = {
            'crm_questionnaire_template': ['questionnaire_name', 'remark'],
            'crm_questionnaire_template_subject': ['subject_title'],
            'crm_subject': ['subject_title'],
            'crm_questionnaire_user_record': ['questionnaire_name', 'external_user_name'],
            'crm_questionnaire_user_submit_result': ['subject_title', 'answer']
        }
        
        for table, fields in chinese_fields.items():
            sample_results = []
            
            # 构建查询语句
            fields_str = ', '.join(['id'] + fields)
            self.source_cursor.execute(f"SELECT {fields_str} FROM {table} ORDER BY RAND() LIMIT 10")
            source_samples = self.source_cursor.fetchall()
            
            for source_record in source_samples:
                pk_value = source_record['id']
                
                # 在目标库中查找对应记录
                self.target_cursor.execute(f"SELECT {fields_str} FROM {table} WHERE id = %s", (pk_value,))
                target_record = self.target_cursor.fetchone()
                
                if target_record:
                    consistent = True
                    differences = []
                    
                    for field in fields:
                        source_value = source_record.get(field)
                        target_value = target_record.get(field)
                        
                        if source_value != target_value:
                            consistent = False
                            differences.append(f"{field}: 源库={source_value}, 目标库={target_value}")
                else:
                    consistent = False
                    differences = ['记录不存在']
                
                sample_results.append({
                    'id': pk_value,
                    'consistent': consistent,
                    'differences': differences
                })
            
            results[table] = {
                'samples': sample_results,
                'consistent_count': sum(1 for r in sample_results if r['consistent']),
                'total_count': len(sample_results)
            }
        
        return results
    
    def verify_relationships(self) -> dict:
        """验证关联关系"""
        results = {}
        
        # 1. template.id -> template_subject.template_id
        self.source_cursor.execute("""
            SELECT t.id, COUNT(ts.id) as count 
            FROM crm_questionnaire_template t 
            LEFT JOIN crm_questionnaire_template_subject ts ON t.id = ts.template_id 
            GROUP BY t.id 
            LIMIT 10
        """)
        source_relationships = self.source_cursor.fetchall()
        
        relationship_results = []
        for source_rel in source_relationships:
            template_id = source_rel['id']
            source_count = source_rel['count']
            
            # 在目标库中查找
            self.target_cursor.execute("""
                SELECT COUNT(id) as count 
                FROM crm_questionnaire_template_subject 
                WHERE template_id = %s
            """, (template_id,))
            target_rel = self.target_cursor.fetchone()
            target_count = target_rel['count'] if target_rel else 0
            
            relationship_results.append({
                'template_id': template_id,
                'source_count': source_count,
                'target_count': target_count,
                'consistent': source_count == target_count
            })
        
        results['template_to_template_subject'] = {
            'samples': relationship_results,
            'consistent_count': sum(1 for r in relationship_results if r['consistent']),
            'total_count': len(relationship_results)
        }
        
        # 2. user_record.id -> user_submit_result.record_id
        self.source_cursor.execute("""
            SELECT ur.id, COUNT(usr.id) as count 
            FROM crm_questionnaire_user_record ur 
            LEFT JOIN crm_questionnaire_user_submit_result usr ON ur.id = usr.record_id 
            GROUP BY ur.id 
            LIMIT 10
        """)
        source_relationships = self.source_cursor.fetchall()
        
        relationship_results = []
        for source_rel in source_relationships:
            record_id = source_rel['id']
            source_count = source_rel['count']
            
            # 在目标库中查找
            self.target_cursor.execute("""
                SELECT COUNT(id) as count 
                FROM crm_questionnaire_user_submit_result 
                WHERE record_id = %s
            """, (record_id,))
            target_rel = self.target_cursor.fetchone()
            target_count = target_rel['count'] if target_rel else 0
            
            relationship_results.append({
                'record_id': record_id,
                'source_count': source_count,
                'target_count': target_count,
                'consistent': source_count == target_count
            })
        
        results['user_record_to_submit_result'] = {
            'samples': relationship_results,
            'consistent_count': sum(1 for r in relationship_results if r['consistent']),
            'total_count': len(relationship_results)
        }
        
        # 3. 同一 external_user_id + questionnaire_name 的填写次数
        self.source_cursor.execute("""
            SELECT external_user_id, questionnaire_name, COUNT(*) as count 
            FROM crm_questionnaire_user_record 
            GROUP BY external_user_id, questionnaire_name 
            HAVING COUNT(*) > 1 
            LIMIT 10
        """)
        source_relationships = self.source_cursor.fetchall()
        
        relationship_results = []
        for source_rel in source_relationships:
            external_user_id = source_rel['external_user_id']
            questionnaire_name = source_rel['questionnaire_name']
            source_count = source_rel['count']
            
            # 在目标库中查找
            self.target_cursor.execute("""
                SELECT COUNT(*) as count 
                FROM crm_questionnaire_user_record 
                WHERE external_user_id = %s AND questionnaire_name = %s
            """, (external_user_id, questionnaire_name))
            target_rel = self.target_cursor.fetchone()
            target_count = target_rel['count'] if target_rel else 0
            
            relationship_results.append({
                'external_user_id': external_user_id,
                'questionnaire_name': questionnaire_name,
                'source_count': source_count,
                'target_count': target_count,
                'consistent': source_count == target_count
            })
        
        results['multiple_submissions'] = {
            'samples': relationship_results,
            'consistent_count': sum(1 for r in relationship_results if r['consistent']),
            'total_count': len(relationship_results)
        }
        
        return results
    
    def generate_table_fingerprint(self, cursor, table: str) -> str:
        """生成表内容指纹"""
        try:
            # 获取主键
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            primary_key = None
            for col in columns:
                if col['Key'] == 'PRI':
                    primary_key = col['Field']
                    break
            
            if not primary_key:
                return ''
            
            # 获取所有字段
            field_names = [col['Field'] for col in columns]
            fields_str = ', '.join(field_names)
            
            # 按主键排序获取所有记录
            cursor.execute(f"SELECT {fields_str} FROM {table} ORDER BY {primary_key}")
            records = cursor.fetchall()
            
            # 生成指纹
            fingerprint = hashlib.md5()
            for record in records:
                # 构建记录字符串
                record_str = '|'.join(str(record.get(field, '')) for field in field_names)
                fingerprint.update(record_str.encode('utf-8'))
            
            return fingerprint.hexdigest()
        except Exception as e:
            print(f"生成表 {table} 指纹失败: {e}")
            return ''
    
    def verify_table_fingerprints(self) -> dict:
        """验证表内容指纹"""
        results = {}
        
        fingerprint_tables = [
            'crm_questionnaire_template',
            'crm_questionnaire_template_subject',
            'crm_subject',
            'crm_questionnaire_user_record',
            'crm_questionnaire_user_submit_result'
        ]
        
        for table in fingerprint_tables:
            source_fingerprint = self.generate_table_fingerprint(self.source_cursor, table)
            target_fingerprint = self.generate_table_fingerprint(self.target_cursor, table)
            
            results[table] = {
                'source_fingerprint': source_fingerprint,
                'target_fingerprint': target_fingerprint,
                'consistent': source_fingerprint == target_fingerprint
            }
        
        return results

def main():
    verifier = ConsistencyVerifier()
    if not verifier.connect():
        return
    
    try:
        # 1. 结构一致性核验
        print("=== 1. 结构一致性核验 ===")
        structure_results = verifier.verify_structure_consistency()
        print("| 表名 | SHOW CREATE TABLE是否一致 | 字段是否一致 | 索引是否一致 | 字符集/排序规则是否一致 | 是否通过 |")
        print("| --- | --- | --- | --- | --- | --- |")
        for table, result in structure_results.items():
            print(f"| {table} | {'是' if result['create_consistent'] else '否'} | {'是' if result['fields_consistent'] else '否'} | {'是' if result['indexes_consistent'] else '否'} | {'是' if result['charset_consistent'] else '否'} | {'是' if result['passed'] else '否'} |")
        
        # 2. 基础数据一致性核验
        print("\n=== 2. 基础数据一致性核验 ===")
        basic_results = verifier.verify_basic_data_consistency()
        print("| 表名 | 源库 COUNT(*) | 目标库 COUNT(*) | 源库 COUNT(DISTINCT 主键) | 目标库 COUNT(DISTINCT 主键) | 是否一致 |")
        print("| --- | ---: | ---: | ---: | ---: | --- |")
        for table, result in basic_results.items():
            print(f"| {table} | {result['source_count']} | {result['target_count']} | {result['source_distinct']} | {result['target_distinct']} | {'是' if result['consistent'] else '否'} |")
        
        # 3. 抽样逐字段比对
        print("\n=== 3. 抽样逐字段比对 ===")
        sample_results = verifier.verify_sample_records(20)
        for table, result in sample_results.items():
            print(f"\n{table}:")
            print(f"  抽样数量: {result['total_count']}")
            print(f"  一致数量: {result['consistent_count']}")
            print(f"  一致率: {result['consistent_rate']:.2f}")
            
            # 输出前5个样本
            print("  前5个样本:")
            for i, sample in enumerate(result['samples'][:5]):
                print(f"    样本 {i+1}:")
                print(f"      主键: {sample['primary_key']}")
                print(f"      一致: {'是' if sample['consistent'] else '否'}")
                if not sample['consistent'] and sample['differences']:
                    print(f"      差异: {sample['differences'][:2]}")
        
        # 4. JSON / 长文本 / 中文核验
        print("\n=== 4. JSON / 长文本 / 中文核验 ===")
        json_results = verifier.verify_json_fields()
        for table, result in json_results.items():
            print(f"\n{table}.subject_content:")
            print(f"  抽样数量: {result['total_count']}")
            print(f"  一致数量: {result['consistent_count']}")
            
            # 输出前5个样本
            print("  前5个样本:")
            for i, sample in enumerate(result['samples'][:5]):
                print(f"    样本 {i+1}:")
                print(f"      ID: {sample['id']}")
                print(f"      源库长度: {sample['source_length']}")
                print(f"      目标库长度: {sample['target_length']}")
                print(f"      一致: {'是' if sample['consistent'] else '否'}")
                print(f"      源库JSON有效: {'是' if sample['source_json_valid'] else '否'}")
                print(f"      目标库JSON有效: {'是' if sample['target_json_valid'] else '否'}")
                print(f"      源库内容: {sample['source_sample']}")
                print(f"      目标库内容: {sample['target_sample']}")
        
        # 中文核验
        chinese_results = verifier.verify_chinese_fields()
        print("\n中文字段核验:")
        for table, result in chinese_results.items():
            print(f"  {table}:")
            print(f"    抽样数量: {result['total_count']}")
            print(f"    一致数量: {result['consistent_count']}")
        
        # 5. 关联关系核验
        print("\n=== 5. 关联关系核验 ===")
        relationship_results = verifier.verify_relationships()
        for rel_name, result in relationship_results.items():
            print(f"\n{rel_name}:")
            print(f"  抽样数量: {result['total_count']}")
            print(f"  一致数量: {result['consistent_count']}")
            
            # 输出前3个样本
            print("  前3个样本:")
            for i, sample in enumerate(result['samples'][:3]):
                print(f"    样本 {i+1}:")
                if 'template_id' in sample:
                    print(f"      template_id: {sample['template_id']}")
                elif 'record_id' in sample:
                    print(f"      record_id: {sample['record_id']}")
                elif 'external_user_id' in sample:
                    print(f"      external_user_id: {sample['external_user_id']}")
                    print(f"      questionnaire_name: {sample['questionnaire_name']}")
                print(f"      源库数量: {sample['source_count']}")
                print(f"      目标库数量: {sample['target_count']}")
                print(f"      一致: {'是' if sample['consistent'] else '否'}")
        
        # 6. 整表内容指纹
        print("\n=== 6. 整表内容指纹 ===")
        fingerprint_results = verifier.verify_table_fingerprints()
        print("| 表名 | 源库哈希 | 目标库哈希 | 是否一致 |")
        print("| --- | --- | --- | --- |")
        for table, result in fingerprint_results.items():
            print(f"| {table} | {result['source_fingerprint']} | {result['target_fingerprint']} | {'是' if result['consistent'] else '否'} |")
        
        # 最终结论
        print("\n=== 最终结论 ===")
        all_passed = True
        for table in TABLES_TO_VERIFY:
            structure_pass = structure_results[table]['passed']
            basic_pass = basic_results[table]['consistent']
            sample_pass = sample_results[table]['consistent_rate'] == 1.0
            
            passed = structure_pass and basic_pass and sample_pass
            all_passed &= passed
            
            if passed:
                print(f"{table}: 完全一致")
            else:
                print(f"{table}: 存在差异")
        
        print(f"\n是否可以进入后端代码修改阶段: {'是' if all_passed else '否'}")
        
    finally:
        verifier.close()

if __name__ == "__main__":
    main()
