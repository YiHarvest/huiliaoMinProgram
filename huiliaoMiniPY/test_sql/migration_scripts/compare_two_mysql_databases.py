import mysql.connector
from typing import List, Dict, Tuple, Any

# 数据库连接配置
ORIGINAL_DB = {
    'host': '117.89.185.157',
    'port': 13049,
    'user': 'jinlong',
    'password': 'jinlong@880208',
    'database': 'huiliao_dev',
    'charset': 'utf8mb4'
}

CURRENT_DB = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

# 需要核对的表
TABLES = [
    'crm_questionnaire_template',
    'crm_questionnaire_template_subject',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

class DatabaseComparator:
    def __init__(self):
        self.original_conn = None
        self.current_conn = None
        self.original_cursor = None
        self.current_cursor = None
    
    def connect(self):
        """连接两个数据库"""
        try:
            self.original_conn = mysql.connector.connect(**ORIGINAL_DB)
            self.current_conn = mysql.connector.connect(**CURRENT_DB)
            self.original_cursor = self.original_conn.cursor(dictionary=True)
            self.current_cursor = self.current_conn.cursor(dictionary=True)
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.original_cursor:
            self.original_cursor.close()
        if self.current_cursor:
            self.current_cursor.close()
        if self.original_conn:
            self.original_conn.close()
        if self.current_conn:
            self.current_conn.close()
    
    def check_tables_exist(self) -> Dict[str, Dict[str, bool]]:
        """检查两个数据库中表是否存在"""
        result = {}
        for table in TABLES:
            result[table] = {
                'original_exists': self._check_table_exists(self.original_cursor, table),
                'current_exists': self._check_table_exists(self.current_cursor, table)
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
    
    def get_table_row_count(self, cursor, table: str) -> int:
        """获取表的总行数"""
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"获取表 {table} 行数失败: {e}")
            return -1
    
    def compare_table_counts(self) -> List[Dict[str, Any]]:
        """对比两个数据库中表的行数"""
        result = []
        for table in TABLES:
            original_count = self.get_table_row_count(self.original_cursor, table)
            current_count = self.get_table_row_count(self.current_cursor, table)
            result.append({
                'table': table,
                'original_count': original_count,
                'current_count': current_count,
                'is_consistent': original_count == current_count
            })
        return result
    
    def get_template_data(self, cursor) -> List[Dict[str, Any]]:
        """获取模板表数据"""
        try:
            cursor.execute("""
                SELECT template_id, questionnaire_name, category, apply_department, group_type
                FROM crm_questionnaire_template
                ORDER BY template_id
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"获取模板表数据失败: {e}")
            return []
    
    def compare_templates(self) -> Dict[str, Any]:
        """对比模板表"""
        original_templates = self.get_template_data(self.original_cursor)
        current_templates = self.get_template_data(self.current_cursor)
        
        # 构建模板ID映射
        original_template_map = {t['template_id']: t for t in original_templates}
        current_template_map = {t['template_id']: t for t in current_templates}
        
        # 找出差异
        original_only = [t for t in original_templates if t['template_id'] not in current_template_map]
        current_only = [t for t in current_templates if t['template_id'] not in original_template_map]
        
        # 找出字段不一致的模板
        inconsistent = []
        for template_id, original in original_template_map.items():
            if template_id in current_template_map:
                current = current_template_map[template_id]
                diffs = []
                for field in ['questionnaire_name', 'category', 'apply_department', 'group_type']:
                    if original.get(field) != current.get(field):
                        diffs.append({
                            'field': field,
                            'original_value': original.get(field),
                            'current_value': current.get(field)
                        })
                if diffs:
                    inconsistent.append({
                        'template_id': template_id,
                        'diffs': diffs
                    })
        
        return {
            'original_only': original_only,
            'current_only': current_only,
            'inconsistent': inconsistent
        }
    
    def get_subject_data(self, cursor) -> List[Dict[str, Any]]:
        """获取题目表数据"""
        try:
            cursor.execute("""
                SELECT template_id, subject_id, sort_order, subject_type, subject_title, subject_content, is_required
                FROM crm_questionnaire_template_subject
                ORDER BY template_id, sort_order
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"获取题目表数据失败: {e}")
            return []
    
    def check_subject_duplicates(self, cursor) -> List[Dict[str, Any]]:
        """检查题目表重复"""
        try:
            cursor.execute("""
                SELECT template_id, subject_id, sort_order, COUNT(*) as count
                FROM crm_questionnaire_template_subject
                GROUP BY template_id, subject_id, sort_order
                HAVING COUNT(*) > 1
                ORDER BY template_id, sort_order
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"检查题目表重复失败: {e}")
            return []
    
    def compare_subjects(self) -> Dict[str, Any]:
        """对比题目表"""
        original_subjects = self.get_subject_data(self.original_cursor)
        current_subjects = self.get_subject_data(self.current_cursor)
        
        # 构建题目唯一键映射
        def get_subject_key(subject):
            return (subject['template_id'], subject['subject_id'], subject['sort_order'])
        
        original_subject_map = {get_subject_key(s): s for s in original_subjects}
        current_subject_map = {get_subject_key(s): s for s in current_subjects}
        
        # 找出差异
        original_only = [s for s in original_subjects if get_subject_key(s) not in current_subject_map]
        current_only = [s for s in current_subjects if get_subject_key(s) not in original_subject_map]
        
        # 找出字段不一致的题目
        inconsistent = []
        for key, original in original_subject_map.items():
            if key in current_subject_map:
                current = current_subject_map[key]
                diffs = []
                for field in ['subject_type', 'subject_title', 'subject_content', 'is_required']:
                    if original.get(field) != current.get(field):
                        diffs.append({
                            'field': field,
                            'original_value': original.get(field),
                            'current_value': current.get(field)
                        })
                if diffs:
                    inconsistent.append({
                        'template_id': original['template_id'],
                        'subject_id': original['subject_id'],
                        'sort_order': original['sort_order'],
                        'diffs': diffs
                    })
        
        return {
            'original_only': original_only,
            'current_only': current_only,
            'inconsistent': inconsistent
        }
    
    def get_template_subject_counts(self, cursor) -> Dict[int, int]:
        """获取每个模板的题目数"""
        try:
            cursor.execute("""
                SELECT template_id, COUNT(*) as count
                FROM crm_questionnaire_template_subject
                GROUP BY template_id
                ORDER BY template_id
            """)
            results = cursor.fetchall()
            return {r['template_id']: r['count'] for r in results}
        except Exception as e:
            print(f"获取模板题目数失败: {e}")
            return {}
    
    def generate_fix_sql(self, template_diff, subject_diff, current_duplicates) -> Dict[str, List[str]]:
        """生成修复SQL"""
        sql = {
            'delete_duplicates': [],
            'insert_templates': [],
            'insert_subjects': [],
            'update_templates': [],
            'update_subjects': []
        }
        
        # 删除重复题目
        for duplicate in current_duplicates:
            template_id = duplicate['template_id']
            subject_id = duplicate['subject_id']
            sort_order = duplicate['sort_order']
            # 保留最小id的记录，删除其他重复
            sql['delete_duplicates'].append(f'''
                DELETE FROM crm_questionnaire_template_subject
                WHERE template_id = {template_id} AND subject_id = {subject_id} AND sort_order = {sort_order}
                AND id NOT IN (
                    SELECT MIN(id) FROM crm_questionnaire_template_subject
                    WHERE template_id = {template_id} AND subject_id = {subject_id} AND sort_order = {sort_order}
                    GROUP BY template_id, subject_id, sort_order
                )
            ''')
        
        # 插入缺少的模板
        for template in template_diff['original_only']:
            template_id = template['template_id']
            questionnaire_name = template['questionnaire_name'].replace('"', '""') if template['questionnaire_name'] else 'NULL'
            category = template['category'].replace('"', '""') if template['category'] else 'NULL'
            apply_department = template['apply_department'].replace('"', '""') if template['apply_department'] else 'NULL'
            group_type = template['group_type'] if template['group_type'] else 0
            
            sql['insert_templates'].append(f'''
                INSERT INTO crm_questionnaire_template (template_id, questionnaire_name, category, apply_department, group_type)
                VALUES ({template_id}, "{questionnaire_name}", "{category}", "{apply_department}", {group_type})
                ON DUPLICATE KEY UPDATE
                questionnaire_name = VALUES(questionnaire_name),
                category = VALUES(category),
                apply_department = VALUES(apply_department),
                group_type = VALUES(group_type)
            ''')
        
        # 插入缺少的题目
        for subject in subject_diff['original_only']:
            template_id = subject['template_id']
            subject_id = subject['subject_id']
            sort_order = subject['sort_order']
            subject_type = subject['subject_type']
            subject_title = subject['subject_title'].replace('"', '""') if subject['subject_title'] else 'NULL'
            subject_content = subject['subject_content'].replace('"', '""') if subject['subject_content'] else 'NULL'
            is_required = subject['is_required'] if subject['is_required'] else 'N'
            
            sql['insert_subjects'].append(f'''
                INSERT INTO crm_questionnaire_template_subject (template_id, subject_id, sort_order, subject_type, subject_title, subject_content, is_required)
                VALUES ({template_id}, {subject_id}, {sort_order}, {subject_type}, "{subject_title}", "{subject_content}", "{is_required}")
                ON DUPLICATE KEY UPDATE
                subject_type = VALUES(subject_type),
                subject_title = VALUES(subject_title),
                subject_content = VALUES(subject_content),
                is_required = VALUES(is_required)
            ''')
        
        # 更新不一致的模板
        for item in template_diff['inconsistent']:
            template_id = item['template_id']
            set_clauses = []
            for diff in item['diffs']:
                field = diff['field']
                value = diff['original_value']
                if value is None:
                    set_clauses.append(f"{field} = NULL")
                elif isinstance(value, str):
                    escaped_value = value.replace('"', '""')
                    set_clauses.append(f"{field} = \"{escaped_value}\"")
                else:
                    set_clauses.append(f"{field} = {value}")
            if set_clauses:
                    set_str = ", ".join(set_clauses)
                    sql['update_templates'].append(f'''
                        UPDATE crm_questionnaire_template
                        SET {set_str}
                        WHERE template_id = {template_id}
                    ''')
        
        # 更新不一致的题目
        for item in subject_diff['inconsistent']:
            template_id = item['template_id']
            subject_id = item['subject_id']
            sort_order = item['sort_order']
            set_clauses = []
            for diff in item['diffs']:
                field = diff['field']
                value = diff['original_value']
                if value is None:
                    set_clauses.append(f"{field} = NULL")
                elif isinstance(value, str):
                    escaped_value = value.replace('"', '""')
                    set_clauses.append(f"{field} = \"{escaped_value}\"")
                else:
                    set_clauses.append(f"{field} = {value}")
            if set_clauses:
                set_str = ", ".join(set_clauses)
                sql['update_subjects'].append(f'''
                    UPDATE crm_questionnaire_template_subject
                    SET {set_str}
                    WHERE template_id = {template_id} AND subject_id = {subject_id} AND sort_order = {sort_order}
                ''')
        
        return sql

def main():
    comparator = DatabaseComparator()
    if not comparator.connect():
        return
    
    try:
        # 一、核对表是否存在
        print("\n一、核对表是否存在")
        table_exists = comparator.check_tables_exist()
        for table, exists in table_exists.items():
            print(f"{table}: 原始库={'存在' if exists['original_exists'] else '不存在'}, 当前库={'存在' if exists['current_exists'] else '不存在'}")
        
        # 二、逐表核对总行数
        print("\n二、逐表核对总行数")
        table_counts = comparator.compare_table_counts()
        print("| 表名 | huiliao_dev | miniprogramYQY | 是否一致 |")
        print("| --- | ---: | ---: | --- |")
        for item in table_counts:
            print(f"| {item['table']} | {item['original_count']} | {item['current_count']} | {'是' if item['is_consistent'] else '否'} |")
        
        # 三、重点核对模板表
        print("\n三、重点核对模板表")
        template_diff = comparator.compare_templates()
        
        print(f"\n1. 原始库有、当前库没有的模板数: {len(template_diff['original_only'])}")
        for template in template_diff['original_only'][:10]:  # 只显示前10个
            print(f"   template_id: {template['template_id']}, name: {template['questionnaire_name']}")
        if len(template_diff['original_only']) > 10:
            print(f"   ... 还有 {len(template_diff['original_only']) - 10} 个模板")
        
        print(f"\n2. 当前库有、原始库没有的模板数: {len(template_diff['current_only'])}")
        for template in template_diff['current_only'][:10]:  # 只显示前10个
            print(f"   template_id: {template['template_id']}, name: {template['questionnaire_name']}")
        if len(template_diff['current_only']) > 10:
            print(f"   ... 还有 {len(template_diff['current_only']) - 10} 个模板")
        
        print(f"\n3. 字段不一致的模板数: {len(template_diff['inconsistent'])}")
        for item in template_diff['inconsistent'][:5]:  # 只显示前5个
            print(f"   template_id: {item['template_id']}")
            for diff in item['diffs']:
                print(f"     {diff['field']}: 原始='{diff['original_value']}', 当前='{diff['current_value']}'")
        if len(template_diff['inconsistent']) > 5:
            print(f"   ... 还有 {len(template_diff['inconsistent']) - 5} 个模板")
        
        # 四、重点核对题目表
        print("\n四、重点核对题目表")
        
        # 检查重复
        print("\n1. 检查重复")
        original_duplicates = comparator.check_subject_duplicates(comparator.original_cursor)
        current_duplicates = comparator.check_subject_duplicates(comparator.current_cursor)
        print(f"   原始库重复题目数: {len(original_duplicates)}")
        print(f"   当前库重复题目数: {len(current_duplicates)}")
        for duplicate in current_duplicates[:5]:  # 只显示前5个
            print(f"     template_id: {duplicate['template_id']}, subject_id: {duplicate['subject_id']}, sort_order: {duplicate['sort_order']}, 重复次数: {duplicate['count']}")
        if len(current_duplicates) > 5:
            print(f"     ... 还有 {len(current_duplicates) - 5} 个重复")
        
        subject_diff = comparator.compare_subjects()
        print(f"\n2. 原始库有、当前库没有的题目数: {len(subject_diff['original_only'])}")
        print(f"3. 当前库有、原始库没有的题目数: {len(subject_diff['current_only'])}")
        print(f"4. 字段不一致的题目数: {len(subject_diff['inconsistent'])}")
        
        # 五、重点输出题目数
        print("\n五、每个模板的题目数")
        original_counts = comparator.get_template_subject_counts(comparator.original_cursor)
        current_counts = comparator.get_template_subject_counts(comparator.current_cursor)
        
        # 找出题目数不一致的模板
        inconsistent_counts = []
        all_template_ids = set(original_counts.keys()) | set(current_counts.keys())
        for template_id in all_template_ids:
            original_count = original_counts.get(template_id, 0)
            current_count = current_counts.get(template_id, 0)
            if original_count != current_count:
                inconsistent_counts.append({
                    'template_id': template_id,
                    'original_count': original_count,
                    'current_count': current_count
                })
        
        print("\n题目数不一致的模板:")
        for item in inconsistent_counts[:10]:  # 只显示前10个
            print(f"template_id: {item['template_id']}, 原始库: {item['original_count']}, 当前库: {item['current_count']}")
        if len(inconsistent_counts) > 10:
            print(f"... 还有 {len(inconsistent_counts) - 10} 个模板")
        
        # 六、生成修复SQL
        print("\n六、生成修复SQL")
        fix_sql = comparator.generate_fix_sql(template_diff, subject_diff, current_duplicates)
        
        print("\nA. 删除当前库多余重复题目的 SQL:")
        for sql_stmt in fix_sql['delete_duplicates'][:5]:  # 只显示前5个
            print(sql_stmt)
            print()
        if len(fix_sql['delete_duplicates']) > 5:
            print(f"... 还有 {len(fix_sql['delete_duplicates']) - 5} 条SQL")
        
        print("\nB. 插入当前库缺少模板的 SQL:")
        for sql_stmt in fix_sql['insert_templates'][:5]:  # 只显示前5个
            print(sql_stmt)
            print()
        if len(fix_sql['insert_templates']) > 5:
            print(f"... 还有 {len(fix_sql['insert_templates']) - 5} 条SQL")
        
        print("\nC. 插入当前库缺少题目的 SQL:")
        for sql_stmt in fix_sql['insert_subjects'][:5]:  # 只显示前5个
            print(sql_stmt)
            print()
        if len(fix_sql['insert_subjects']) > 5:
            print(f"... 还有 {len(fix_sql['insert_subjects']) - 5} 条SQL")
        
        print("\nD. 更新当前库字段不一致记录的 SQL:")
        for sql_stmt in fix_sql['update_templates'][:5]:  # 只显示前5个
            print(sql_stmt)
            print()
        for sql_stmt in fix_sql['update_subjects'][:5]:  # 只显示前5个
            print(sql_stmt)
            print()
        if len(fix_sql['update_templates']) + len(fix_sql['update_subjects']) > 10:
            print(f"... 还有更多更新SQL")
        
        # 七、添加唯一索引
        print("\n七、添加唯一索引:")
        print("""
        ALTER TABLE crm_questionnaire_template_subject
        ADD UNIQUE KEY uk_template_subject_sort (template_id, subject_id, sort_order);
        """)
        
        # 八、最终结论
        print("\n八、最终结论")
        is_consistent = all(item['is_consistent'] for item in table_counts)
        print(f"1. 两个库是否一致: {'是' if is_consistent else '否'}")
        print(f"2. 当前库缺少: {len(template_diff['original_only'])} 个模板, {len(subject_diff['original_only'])} 个题目")
        print(f"3. 当前库多了: {len(template_diff['current_only'])} 个模板, {len(subject_diff['current_only'])} 个题目")
        print(f"4. 当前库不一致: {len(template_diff['inconsistent'])} 个模板, {len(subject_diff['inconsistent'])} 个题目, {len(current_duplicates)} 个重复题目")
        print("5. 执行顺序建议:")
        print("   a. 先执行删除重复题目的SQL (A)")
        print("   b. 再执行插入缺少模板的SQL (B)")
        print("   c. 然后执行插入缺少题目的SQL (C)")
        print("   d. 最后执行更新不一致记录的SQL (D)")
        print("   e. 完成后执行添加唯一索引的SQL")
        
    finally:
        comparator.close()

if __name__ == "__main__":
    main()
