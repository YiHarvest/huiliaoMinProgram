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

# 要分析的表
TABLES_TO_ANALYZE = [
    'crm_questionnaire_template',
    'crm_questionnaire_template_subject',
    'crm_subject',
    'crm_questionnaire_user_record',
    'crm_questionnaire_user_subject_record',
    'crm_questionnaire_user_submit_result',
    'crm_questionnaire_user_submit_result_analysis'
]

class QuestionnaireSystemAnalyzer:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = mysql.connector.connect(**SOURCE_DB)
            self.cursor = self.conn.cursor(dictionary=True)
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def get_table_structure(self, table: str) -> List[Dict[str, Any]]:
        """获取表结构"""
        try:
            self.cursor.execute(f"DESCRIBE {table}")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取表 {table} 结构失败: {e}")
            return []
    
    def get_table_comment(self, table: str) -> str:
        """获取表注释"""
        try:
            self.cursor.execute(f"""
                SELECT table_comment 
                FROM information_schema.tables 
                WHERE table_schema = 'huiliao_dev' 
                AND table_name = '{table}'
            """)
            result = self.cursor.fetchone()
            return result['table_comment'] if result else ''
        except Exception as e:
            print(f"获取表 {table} 注释失败: {e}")
            return ''
    
    def analyze_table(self, table: str) -> Dict[str, Any]:
        """分析表"""
        structure = self.get_table_structure(table)
        comment = self.get_table_comment(table)
        
        # 提取主键
        primary_key = None
        for field in structure:
            if field['Key'] == 'PRI':
                primary_key = field['Field']
                break
        
        # 提取外键/关联字段
        foreign_keys = []
        for field in structure:
            field_name = field['Field']
            if any(keyword in field_name.lower() for keyword in ['id', 'template', 'subject', 'record']):
                if field_name != primary_key:
                    foreign_keys.append(field_name)
        
        # 分析关联关系
        relationships = []
        if 'template_id' in [f['Field'] for f in structure]:
            relationships.append({
                'related_table': 'crm_questionnaire_template',
                'foreign_key': 'template_id',
                'primary_key': 'id',
                'condition': 'template_id = id'
            })
        if 'subject_id' in [f['Field'] for f in structure]:
            relationships.append({
                'related_table': 'crm_subject',
                'foreign_key': 'subject_id',
                'primary_key': 'id',
                'condition': 'subject_id = id'
            })
        if 'record_id' in [f['Field'] for f in structure]:
            relationships.append({
                'related_table': 'crm_questionnaire_user_record',
                'foreign_key': 'record_id',
                'primary_key': 'id',
                'condition': 'record_id = id'
            })
        
        # 分析在流程中的作用
        role = self._analyze_role(table)
        
        return {
            'table_name': table,
            'table_comment': comment,
            'primary_key': primary_key,
            'foreign_keys': foreign_keys,
            'relationships': relationships,
            'role': role
        }
    
    def _analyze_role(self, table: str) -> str:
        """分析表在流程中的作用"""
        table_lower = table.lower()
        if 'template' in table_lower and 'subject' not in table_lower:
            return '存储量表模板基本信息，是整个量表体系的基础'
        elif 'template_subject' in table_lower:
            return '存储模板与题目的关联关系，定义每个模板包含哪些题目'
        elif 'subject' == table_lower:
            return '存储题目基本信息，包括题目类型、标题、内容等'
        elif 'user_record' in table_lower and 'subject' not in table_lower:
            return '存储用户填写量表的记录，是用户与量表交互的核心表'
        elif 'user_subject_record' in table_lower:
            return '存储用户填写过程中每个题目的记录'
        elif 'submit_result' in table_lower and 'analysis' not in table_lower:
            return '存储用户提交的最终答案结果'
        elif 'submit_result_analysis' in table_lower:
            return '存储对用户提交结果的分析报告'
        return '未知作用'
    
    def check_question_options(self):
        """检查题目选项存储位置"""
        print("\n=== 检查题目选项存储位置 ===")
        
        # 检查 crm_subject 表
        print("\n1. 检查 crm_subject 表结构")
        subject_structure = self.get_table_structure('crm_subject')
        for field in subject_structure:
            print(f"  {field['Field']}: {field['Type']}")
        
        # 检查 crm_subject 中的内容字段
        print("\n2. 检查 crm_subject 中的内容字段样例")
        try:
            self.cursor.execute("SELECT id, subject_title, subject_content FROM crm_subject LIMIT 3")
            samples = self.cursor.fetchall()
            for sample in samples:
                print(f"  题目ID: {sample['id']}")
                print(f"  题目标题: {sample['subject_title']}")
                print(f"  题目内容: {sample['subject_content'][:200]}..." if sample['subject_content'] else "  题目内容: 空")
                print()
        except Exception as e:
            print(f"  错误: {e}")
        
        # 检查 sys_dict_item 表
        print("\n3. 检查 sys_dict_item 表结构")
        try:
            self.cursor.execute("DESCRIBE sys_dict_item")
            dict_structure = self.cursor.fetchall()
            for field in dict_structure:
                print(f"  {field['Field']}: {field['Type']}")
        except Exception as e:
            print(f"  错误: {e}")
        
        # 检查是否有其他选项表
        print("\n4. 检查是否有其他选项相关表")
        try:
            self.cursor.execute("""
                SELECT table_name, table_comment 
                FROM information_schema.tables 
                WHERE table_schema = 'huiliao_dev' 
                AND table_name LIKE '%option%' OR table_name LIKE '%choice%'
            """)
            option_tables = self.cursor.fetchall()
            if option_tables:
                for table in option_tables:
                    print(f"  {table['TABLE_NAME']}: {table['TABLE_COMMENT']}")
            else:
                print("  没有找到选项相关的表")
        except Exception as e:
            print(f"  错误: {e}")
    
    def check_multiple_submissions(self):
        """检查是否支持多次填写"""
        print("\n=== 检查是否支持多次填写 ===")
        
        # 检查同一个用户对同一个模板是否有多次记录
        try:
            self.cursor.execute("""
                SELECT external_user_id, questionnaire_name, COUNT(*) as submit_count 
                FROM crm_questionnaire_user_record 
                GROUP BY external_user_id, questionnaire_name 
                HAVING COUNT(*) > 1 
                LIMIT 5
            """)
            multiple_submissions = self.cursor.fetchall()
            
            if multiple_submissions:
                print("\n1. 存在多次填写的记录:")
                for record in multiple_submissions:
                    print(f"  用户: {record['external_user_id']}, 量表: {record['questionnaire_name']}, 填写次数: {record['submit_count']}")
            else:
                print("\n1. 没有找到多次填写的记录")
            
            # 检查记录的创建时间
            print("\n2. 检查记录的创建时间:")
            self.cursor.execute("""
                SELECT id, external_user_id, questionnaire_name, create_time 
                FROM crm_questionnaire_user_record 
                ORDER BY external_user_id, questionnaire_name, create_time 
                LIMIT 10
            """)
            time_records = self.cursor.fetchall()
            for record in time_records:
                print(f"  记录ID: {record['id']}, 用户: {record['external_user_id']}, 量表: {record['questionnaire_name']}, 创建时间: {record['create_time']}")
            
        except Exception as e:
            print(f"  错误: {e}")
    
    def run_analysis(self):
        """运行分析"""
        if not self.connect():
            return
        
        try:
            # 分析每张表
            print("=== 分析量表体系表结构和关联关系 ===")
            table_analyses = []
            for table in TABLES_TO_ANALYZE:
                analysis = self.analyze_table(table)
                table_analyses.append(analysis)
                
                print(f"\n表名: {analysis['table_name']}")
                print(f"表注释: {analysis['table_comment']}")
                print(f"主键: {analysis['primary_key']}")
                print(f"关键外键/关联字段: {analysis['foreign_keys']}")
                print("关联关系:")
                for rel in analysis['relationships']:
                    print(f"  与 {rel['related_table']} 关联")
                    print(f"  关联条件: {rel['foreign_key']} = {rel['primary_key']}")
                print(f"在量表填写流程中的作用: {analysis['role']}")
            
            # 检查题目选项存储位置
            self.check_question_options()
            
            # 检查是否支持多次填写
            self.check_multiple_submissions()
            
            # 给出结论
            self._give_conclusion()
            
        finally:
            self.close()
    
    def _give_conclusion(self):
        """给出结论"""
        print("\n=== 结论 ===")
        print("为了支持小程序完整量表流程，最少必须同步的表:")
        print("1. crm_questionnaire_template - 量表模板表，用于展示量表列表")
        print("2. crm_questionnaire_template_subject - 模板题目关联表，用于展示模板包含的题目")
        print("3. crm_subject - 题目表，用于存储题目详情")
        print("4. crm_questionnaire_user_record - 用户记录表，用于记录用户填写行为")
        print("5. crm_questionnaire_user_submit_result - 用户提交结果表，用于存储用户答案")
        print("6. crm_questionnaire_user_submit_result_analysis - 分析结果表，用于展示分析报告")
        
        print("\n建议同步但非必须的表:")
        print("1. crm_questionnaire_user_subject_record - 用户题目记录表，用于记录填写过程")
        print("2. sys_dict_item - 字典项表，可能用于存储选项值")
        
        print("\n重要说明:")
        print("- 题目选项很可能存储在 crm_subject 的 subject_content 字段中，以 JSON 或其他格式存储")
        print("- crm_questionnaire_user_record 支持多次填写，通过为每次填写生成新记录来实现")
        print("- 区分多次填写的方式是通过记录的创建时间和记录ID")

def main():
    analyzer = QuestionnaireSystemAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
