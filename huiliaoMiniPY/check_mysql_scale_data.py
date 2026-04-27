import mysql.connector
import json
from config import config

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

try:
    # 连接MySQL数据库
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    # 测试的量表名称
    scale_names = [
        "失眠程度自评量表",
        "国际勃起功能评分5项(IIEF-5)",
        "男性不育病史采集表",
        "中医妇科健康状态问诊表",
        "前列腺炎病史采集表"
    ]
    
    for scale_name in scale_names:
        print(f"\n=== 检查量表: {scale_name} ===")
        
        # 1. 检查量表是否存在
        cursor.execute("SELECT id FROM crm_questionnaire_template WHERE questionnaire_name = %s", (scale_name,))
        template = cursor.fetchone()
        
        if not template:
            print("  未找到量表")
            continue
        
        template_id = template['id']
        print(f"  量表ID: {template_id}")
        
        # 2. 检查是否有对应的题目
        cursor.execute(
            "SELECT id, subject_title, subject_type, subject_content, is_required, sort_order FROM crm_questionnaire_template_subject WHERE template_id = %s ORDER BY sort_order",
            (template_id,)
        )
        subjects = cursor.fetchall()
        
        print(f"  题目数量: {len(subjects)}")
        
        if subjects:
            print("  前3道题的题目标题:")
            for i, subject in enumerate(subjects[:3], 1):
                print(f"    {i}. {subject['subject_title']}")
            
            # 输出第一道题的选项
            first_subject = subjects[0]
            if first_subject['subject_content']:
                try:
                    options = json.loads(first_subject['subject_content'])
                    print("  第一道题的选项内容:")
                    for j, opt in enumerate(options, 1):
                        print(f"    {j}. {opt.get('label')}: {opt.get('value')}")
                except json.JSONDecodeError:
                    print("  选项内容不是有效的JSON")
        else:
            print("  无题目")
    
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
