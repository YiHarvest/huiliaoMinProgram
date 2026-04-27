import mysql.connector
from config import config
from db import start_questionnaire

# MySQL连接配置
MYSQL_CONFIG = {
    'host': config.get('database', {}).get('mysql', {}).get('host', '192.168.1.208'),
    'port': config.get('database', {}).get('mysql', {}).get('port', 13060),
    'user': config.get('database', {}).get('mysql', {}).get('user', 'miniprogramYQY'),
    'password': config.get('database', {}).get('mysql', {}).get('password', 'yqy123456'),
    'database': config.get('database', {}).get('mysql', {}).get('database', 'miniprogramYQY'),
    'charset': 'utf8mb4',
    'autocommit': True,
    'ssl_disabled': True
}

# 测试的 templateId
test_templates = [
    2044969684322750465,  # 不育症诊断量表（第一次填表请选择这个表）
    2042879199571611650,  # 国际前列腺症状评分表I-PSS（第一次填表请选择这个表）
    2044968508025999362,  # 早泄诊断量表（PEDT）（第一次填表请选择这个表）
]

external_user_id = "test_user_final"

try:
    # 连接MySQL数据库
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    print("=== 验证 3 个 templateId ===\n")
    
    for i, template_id in enumerate(test_templates):
        print(f"[{i+1}] 测试 templateId: {template_id}")
        
        # 1. 验证 templateId 在 MySQL 中存在
        cursor.execute(
            "SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE id = %s",
            (template_id,)
        )
        template = cursor.fetchone()
        
        if template:
            print(f"  [OK] 模板存在: {template['questionnaire_name']}")
        else:
            print(f"  [FAIL] 模板不存在")
            continue
        
        # 2. 调用 start 接口
        try:
            record_id = start_questionnaire(external_user_id, template_id)
            print(f"  [OK] start 接口返回 recordId: {record_id}")
            
            # 3. 验证 recordId 在 MySQL 中存在
            cursor.execute(
                "SELECT id, external_user_id, questionnaire_name FROM crm_questionnaire_user_record WHERE id = %s",
                (record_id,)
            )
            record = cursor.fetchone()
            
            if record:
                print(f"  [OK] recordId 在 MySQL 中存在: {record['questionnaire_name']}")
            else:
                print(f"  [FAIL] recordId 在 MySQL 中不存在")
        except Exception as e:
            print(f"  [FAIL] start 接口调用失败: {e}")
        
        print()
    
    cursor.close()
    connection.close()
    
    print("=== 验证完成 ===")
    
except Exception as e:
    print(f"错误: {e}")
