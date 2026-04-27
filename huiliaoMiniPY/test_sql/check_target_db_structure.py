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

class DatabaseChecker:
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
    
    def get_table_structure(self, cursor, table: str) -> List[Dict[str, Any]]:
        """获取表结构"""
        try:
            cursor.execute(f"DESCRIBE {table}")
            return cursor.fetchall()
        except Exception as e:
            print(f"获取表 {table} 结构失败: {e}")
            return []
    
    def check_tables_exist(self) -> Dict[str, Dict[str, bool]]:
        """检查两个数据库中表是否存在"""
        result = {}
        for table in TABLES:
            result[table] = {
                'source_exists': self._check_table_exists(self.source_cursor, table),
                'target_exists': self._check_table_exists(self.target_cursor, table)
            }
        return result
    
    def _check_table_exists(self, cursor, table: str) -> bool:
        """检查单个表是否存在"""
        try:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"检查表 {table} 失败: {e}")
            return False
    
    def compare_table_structures(self) -> Dict[str, Dict[str, Any]]:
        """对比两个数据库中表的结构"""
        result = {}
        for table in TABLES:
            source_structure = self.get_table_structure(self.source_cursor, table)
            target_structure = self.get_table_structure(self.target_cursor, table)
            
            source_fields = {field['Field']: field for field in source_structure}
            target_fields = {field['Field']: field for field in target_structure}
            
            # 检查字段差异
            source_only = list(set(source_fields.keys()) - set(target_fields.keys()))
            target_only = list(set(target_fields.keys()) - set(source_fields.keys()))
            
            # 检查字段类型差异
            type_diff = []
            for field, source_type in source_fields.items():
                if field in target_fields:
                    target_type = target_fields[field]
                    if source_type['Type'] != target_type['Type']:
                        type_diff.append({
                            'field': field,
                            'source_type': source_type['Type'],
                            'target_type': target_type['Type']
                        })
            
            result[table] = {
                'source_fields': source_fields,
                'target_fields': target_fields,
                'source_only': source_only,
                'target_only': target_only,
                'type_diff': type_diff
            }
        return result
    
    def get_table_row_count(self, cursor, table: str) -> int:
        """获取表的总行数"""
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"获取表 {table} 行数失败: {e}")
            return -1

def main():
    checker = DatabaseChecker()
    if not checker.connect():
        return
    
    try:
        # 检查表是否存在
        print("\n一、检查表是否存在")
        table_exists = checker.check_tables_exist()
        for table, exists in table_exists.items():
            print(f"{table}: 源库={'存在' if exists['source_exists'] else '不存在'}, 目标库={'存在' if exists['target_exists'] else '不存在'}")
        
        # 对比表结构
        print("\n二、对比表结构")
        structure_diff = checker.compare_table_structures()
        
        for table, diff in structure_diff.items():
            print(f"\n{table}:")
            print(f"  源库字段数: {len(diff['source_fields'])}")
            print(f"  目标库字段数: {len(diff['target_fields'])}")
            
            if diff['source_only']:
                print(f"  源库有、目标库没有的字段: {diff['source_only']}")
            if diff['target_only']:
                print(f"  目标库有、源库没有的字段: {diff['target_only']}")
            if diff['type_diff']:
                print("  字段类型差异:")
                for item in diff['type_diff']:
                    print(f"    {item['field']}: 源库='{item['source_type']}', 目标库='{item['target_type']}'")
        
        # 检查源库表的行数
        print("\n三、源库表行数")
        for table in TABLES:
            count = checker.get_table_row_count(checker.source_cursor, table)
            print(f"{table}: {count} 行")
        
    finally:
        checker.close()

if __name__ == "__main__":
    main()
