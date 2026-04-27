import mysql.connector
from typing import List, Dict, Any

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

# 需要导入的表
TABLES = [
    'crm_qw_external_contact',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_submit_result_analysis',
    'crm_qw_work_message',
    'crm_qw_msg_audit',
    'crm_customer_message_attach',
    'crm_message_attach_analysis'
]

class TableCreator:
    def __init__(self):
        self.source_conn = None
        self.target_conn = None
        self.source_cursor = None
        self.target_cursor = None
        self.create_statements = {}
    
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
    
    def execute_create_tables(self):
        """执行建表操作"""
        results = {}
        
        # 获取源库的创建语句
        for table in TABLES:
            create_stmt = self.get_create_table_statement(self.source_cursor, table)
            if create_stmt:
                self.create_statements[table] = create_stmt
                print(f"获取 {table} 创建语句成功")
            else:
                print(f"获取 {table} 创建语句失败")
        
        # 在目标库中创建表
        for table, create_stmt in self.create_statements.items():
            success = self.create_table(self.target_cursor, create_stmt)
            results[table] = success
            if success:
                print(f"创建 {table} 成功")
            else:
                print(f"创建 {table} 失败")
        
        # 提交事务
        if self.target_conn:
            self.target_conn.commit()
        
        return results
    
    def compare_table_structures(self) -> Dict[str, Dict[str, Any]]:
        """对比表结构"""
        results = {}
        
        for table in TABLES:
            # 获取源库和目标库的创建语句
            source_create = self.get_create_table_statement(self.source_cursor, table)
            target_create = self.get_create_table_statement(self.target_cursor, table)
            
            # 检查字段一致性
            source_fields = self._extract_fields(source_create)
            target_fields = self._extract_fields(target_create)
            fields_consistent = self._compare_fields(source_fields, target_fields)
            
            # 检查索引一致性
            source_indexes = self._extract_indexes(source_create)
            target_indexes = self._extract_indexes(target_create)
            indexes_consistent = self._compare_indexes(source_indexes, target_indexes)
            
            # 检查字符集和排序规则
            source_charset = self._extract_charset(source_create)
            target_charset = self._extract_charset(target_create)
            charset_consistent = source_charset == target_charset
            
            # 检查整体一致性
            overall_consistent = fields_consistent and indexes_consistent and charset_consistent
            
            results[table] = {
                'source_create': source_create,
                'target_create': target_create,
                'source_exists': source_create is not None,
                'target_exists': target_create is not None,
                'fields_consistent': fields_consistent,
                'indexes_consistent': indexes_consistent,
                'charset_consistent': charset_consistent,
                'overall_consistent': overall_consistent,
                'source_fields': source_fields,
                'target_fields': target_fields,
                'source_indexes': source_indexes,
                'target_indexes': target_indexes,
                'source_charset': source_charset,
                'target_charset': target_charset
            }
        
        return results
    
    def _extract_fields(self, create_statement: str) -> List[Dict[str, Any]]:
        """从创建语句中提取字段信息"""
        if not create_statement:
            return []
        
        fields = []
        # 简单解析字段定义
        lines = create_statement.split('\n')
        in_fields = False
        for line in lines:
            line = line.strip()
            if line.startswith('CREATE TABLE'):
                in_fields = True
                continue
            if in_fields:
                if line.startswith(')'):
                    break
                if line.endswith(','):
                    line = line[:-1]
                # 跳过约束和索引
                if any(keyword in line.lower() for keyword in ['primary key', 'unique key', 'key ', 'index']):
                    continue
                # 提取字段名和类型
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    field_name = parts[0]
                    field_def = parts[1]
                    fields.append({'name': field_name, 'definition': field_def})
        
        return fields
    
    def _extract_indexes(self, create_statement: str) -> List[Dict[str, Any]]:
        """从创建语句中提取索引信息"""
        if not create_statement:
            return []
        
        indexes = []
        lines = create_statement.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('PRIMARY KEY') or line.startswith('UNIQUE KEY') or line.startswith('KEY ') or line.startswith('INDEX'):
                indexes.append(line)
        
        return indexes
    
    def _extract_charset(self, create_statement: str) -> Dict[str, str]:
        """从创建语句中提取字符集和排序规则"""
        if not create_statement:
            return {}
        
        charset = {}
        lines = create_statement.split('\n')
        for line in lines:
            line = line.strip()
            if 'CHARSET=' in line:
                parts = line.split('CHARSET=')
                if len(parts) >= 2:
                    charset_part = parts[1].split()[0]
                    if charset_part.endswith(','):
                        charset_part = charset_part[:-1]
                    charset['charset'] = charset_part
            if 'COLLATE=' in line:
                parts = line.split('COLLATE=')
                if len(parts) >= 2:
                    collate_part = parts[1].split()[0]
                    if collate_part.endswith(','):
                        collate_part = collate_part[:-1]
                    charset['collate'] = collate_part
        
        return charset
    
    def _compare_fields(self, source_fields: List[Dict[str, Any]], target_fields: List[Dict[str, Any]]) -> bool:
        """比较字段是否一致"""
        if len(source_fields) != len(target_fields):
            return False
        
        for i, (source_field, target_field) in enumerate(zip(source_fields, target_fields)):
            if source_field['name'] != target_field['name']:
                return False
            # 忽略默认值中的时间戳差异
            source_def = source_field['definition']
            target_def = target_field['definition']
            if source_def != target_def:
                return False
        
        return True
    
    def _compare_indexes(self, source_indexes: List[str], target_indexes: List[str]) -> bool:
        """比较索引是否一致"""
        return source_indexes == target_indexes

def main():
    creator = TableCreator()
    if not creator.connect():
        return
    
    try:
        # 执行建表
        print("\n一、执行建表操作")
        create_results = creator.execute_create_tables()
        
        # 对比表结构
        print("\n二、对比表结构")
        structure_results = creator.compare_table_structures()
        
        # 输出建表执行情况
        print("\n1. 建表执行情况")
        print("| 表名 | 建表是否成功 | 备注 |")
        print("| --- | --- | --- |")
        for table, success in create_results.items():
            remark = "成功" if success else "失败"
            print(f"| {table} | {'是' if success else '否'} | {remark} |")
        
        # 输出结构核对结果
        print("\n2. 结构核对结果")
        print("| 表名 | 源库存在 | 目标库存在 | 字段是否一致 | 索引是否一致 | 字符集/排序规则是否一致 | 是否可进入导数阶段 |")
        print("| --- | --- | --- | --- | --- | --- | --- |")
        
        all_consistent = True
        for table, result in structure_results.items():
            overall_consistent = result['overall_consistent']
            all_consistent &= overall_consistent
            print(f"| {table} | {'是' if result['source_exists'] else '否'} | {'是' if result['target_exists'] else '否'} | {'是' if result['fields_consistent'] else '否'} | {'是' if result['indexes_consistent'] else '否'} | {'是' if result['charset_consistent'] else '否'} | {'是' if overall_consistent else '否'} |")
        
        # 输出每张表的差异说明
        print("\n3. 每张表的差异说明")
        for table, result in structure_results.items():
            print(f"\n{table}:")
            print(f"  源库创建语句:")
            print(f"  {result['source_create']}")
            print(f"  目标库创建语句:")
            print(f"  {result['target_create']}")
            
            if not result['fields_consistent']:
                print("  字段差异:")
                for i, (source_field, target_field) in enumerate(zip(result['source_fields'], result['target_fields'])):
                    if source_field['name'] != target_field['name']:
                        print(f"    字段名: 源库='{source_field['name']}', 目标库='{target_field['name']}'")
                    elif source_field['definition'] != target_field['definition']:
                        print(f"    字段定义: 源库='{source_field['definition']}', 目标库='{target_field['definition']}'")
            
            if not result['indexes_consistent']:
                print("  索引差异:")
                for i, (source_index, target_index) in enumerate(zip(result['source_indexes'], result['target_indexes'])):
                    if source_index != target_index:
                        print(f"    索引 {i+1}: 源库='{source_index}', 目标库='{target_index}'")
            
            if not result['charset_consistent']:
                print("  字符集差异:")
                print(f"    源库: {result['source_charset']}")
                print(f"    目标库: {result['target_charset']}")
        
        # 最终结论
        print("\n4. 最终结论")
        if all_consistent:
            print("所有表结构核对通过，可以进入数据同步阶段")
        else:
            print("表结构核对未通过，需要修复差异后再进行数据同步")
        
    finally:
        creator.close()

if __name__ == "__main__":
    main()
