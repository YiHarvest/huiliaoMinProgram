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

# 关键词列表
KEYWORDS = ['questionnaire', 'question', 'option', 'answer', 'scale', 'subject', 'item', 'template']

class TableSearcher:
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
    
    def search_tables(self, cursor, database: str) -> List[Dict[str, Any]]:
        """搜索包含关键词的表"""
        tables = []
        
        # 搜索表名包含关键词的表
        for keyword in KEYWORDS:
            try:
                query = f"""
                SELECT table_name, table_comment 
                FROM information_schema.tables 
                WHERE table_schema = '{database}' 
                AND table_name LIKE '%{keyword}%'
                """
                cursor.execute(query)
                results = cursor.fetchall()
                for result in results:
                    tables.append({
                        'table_name': result['TABLE_NAME'],
                        'table_comment': result['TABLE_COMMENT'] or '',
                        'keyword': keyword
                    })
            except Exception as e:
                print(f"搜索表失败: {e}")
        
        # 去重
        seen_tables = set()
        unique_tables = []
        for table in tables:
            if table['table_name'] not in seen_tables:
                seen_tables.add(table['table_name'])
                unique_tables.append(table)
        
        return unique_tables
    
    def get_table_columns(self, cursor, table: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        try:
            cursor.execute(f"DESCRIBE {table}")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'field': row['Field'],
                    'type': row['Type'],
                    'null': row['Null'],
                    'key': row['Key'],
                    'default': row['Default'],
                    'extra': row['Extra']
                })
            return columns
        except Exception as e:
            print(f"获取表 {table} 列信息失败: {e}")
            return []
    
    def analyze_table(self, table_name: str, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析表的业务作用"""
        analysis = {
            'key_fields': [],
            'business_role': '',
            'related_to': {
                'list_display': False,
                'questions_display': False,
                'save_submission': False,
                'secondary_fill': False,
                'history_view': False
            }
        }
        
        # 提取关键字段
        for col in columns:
            if col['key'] == 'PRI':
                analysis['key_fields'].append(col['field'])
            elif any(keyword in col['field'].lower() for keyword in ['id', 'name', 'title', 'content', 'template', 'subject', 'option', 'answer', 'user', 'record']):
                analysis['key_fields'].append(col['field'])
        
        # 分析业务作用
        table_lower = table_name.lower()
        if 'template' in table_lower or 'questionnaire' in table_lower:
            analysis['business_role'] = '量表模板/定义表'
            analysis['related_to']['list_display'] = True
        elif 'subject' in table_lower or 'question' in table_lower:
            analysis['business_role'] = '量表题目表'
            analysis['related_to']['questions_display'] = True
        elif 'option' in table_lower:
            analysis['business_role'] = '题目选项表'
            analysis['related_to']['questions_display'] = True
        elif 'answer' in table_lower:
            analysis['business_role'] = '用户答案表'
            analysis['related_to']['save_submission'] = True
            analysis['related_to']['history_view'] = True
        elif 'record' in table_lower:
            analysis['business_role'] = '用户记录表'
            analysis['related_to']['save_submission'] = True
            analysis['related_to']['history_view'] = True
            analysis['related_to']['secondary_fill'] = True
        
        return analysis
    
    def run_analysis(self):
        """运行分析"""
        if not self.connect():
            return
        
        try:
            # 搜索源库表
            print("\n=== 源库 huiliao_dev 分析 ===")
            source_tables = self.search_tables(self.source_cursor, 'huiliao_dev')
            self._print_table_analysis(self.source_cursor, source_tables)
            
            # 搜索目标库表
            print("\n=== 目标库 miniprogramYQY 分析 ===")
            target_tables = self.search_tables(self.target_cursor, 'miniprogramYQY')
            self._print_table_analysis(self.target_cursor, target_tables)
            
            # 对比分析
            self._compare_analysis(source_tables, target_tables)
            
        finally:
            self.close()
    
    def _print_table_analysis(self, cursor, tables: List[Dict[str, Any]]):
        """打印表分析结果"""
        if not tables:
            print("未找到相关表")
            return
        
        for table in tables:
            table_name = table['table_name']
            table_comment = table['table_comment']
            
            print(f"\n表名: {table_name}")
            print(f"表注释: {table_comment}")
            
            # 获取列信息
            columns = self.get_table_columns(cursor, table_name)
            
            # 分析表
            analysis = self.analyze_table(table_name, columns)
            
            # 打印关键字段
            print("关键字段:", analysis['key_fields'])
            
            # 打印业务作用
            print("业务作用:", analysis['business_role'])
            
            # 打印相关需求
            print("相关需求:")
            for key, value in analysis['related_to'].items():
                if value:
                    print(f"  - {self._get_requirement_name(key)}")
    
    def _get_requirement_name(self, key: str) -> str:
        """获取需求名称"""
        requirement_map = {
            'list_display': '前端展示量表列表',
            'questions_display': '前端展示题目和选项',
            'save_submission': '保存用户提交',
            'secondary_fill': '支持二次填写',
            'history_view': '查看历史填写记录'
        }
        return requirement_map.get(key, key)
    
    def _compare_analysis(self, source_tables: List[Dict[str, Any]], target_tables: List[Dict[str, Any]]):
        """对比分析"""
        source_table_names = {table['table_name'] for table in source_tables}
        target_table_names = {table['table_name'] for table in target_tables}
        
        missing_in_target = source_table_names - target_table_names
        
        print("\n=== 对比分析 ===")
        print(f"源库中有但目标库中没有的表: {missing_in_target}")
        
        # 评估是否足以支持完整流程
        print("\n=== 流程支持评估 ===")
        
        # 检查是否有量表模板表
        has_template = any('template' in table['table_name'].lower() or 'questionnaire' in table['table_name'].lower() for table in target_tables)
        
        # 检查是否有题目表
        has_subject = any('subject' in table['table_name'].lower() or 'question' in table['table_name'].lower() for table in target_tables)
        
        # 检查是否有选项表
        has_option = any('option' in table['table_name'].lower() for table in target_tables)
        
        # 检查是否有用户记录表
        has_record = any('record' in table['table_name'].lower() for table in target_tables)
        
        # 检查是否有答案表
        has_answer = any('answer' in table['table_name'].lower() for table in target_tables)
        
        print(f"是否有量表模板表: {'是' if has_template else '否'}")
        print(f"是否有题目表: {'是' if has_subject else '否'}")
        print(f"是否有选项表: {'是' if has_option else '否'}")
        print(f"是否有用户记录表: {'是' if has_record else '否'}")
        print(f"是否有答案表: {'是' if has_answer else '否'}")
        
        # 评估完整性
        if has_template and has_subject and has_record and has_answer:
            print("\n评估结果: 基本足以支持完整的小程序量表填写流程")
        else:
            print("\n评估结果: 不足以支持完整的小程序量表填写流程")
            if not has_template:
                print("  缺少: 量表模板表")
            if not has_subject:
                print("  缺少: 题目表")
            if not has_option:
                print("  缺少: 选项表")
            if not has_record:
                print("  缺少: 用户记录表")
            if not has_answer:
                print("  缺少: 答案表")

def main():
    searcher = TableSearcher()
    searcher.run_analysis()

if __name__ == "__main__":
    main()
