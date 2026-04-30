import json
import requests

# 测试的量表templateId
scale_templates = [
    {"name": "失眠程度自评量表", "templateId": 2012775335111716865},
    {"name": "国际勃起功能评分5项(IIEF-5)", "templateId": 2013810071253364738},
    {"name": "男性不育病史采集表", "templateId": 2014255987972739073},
    {"name": "中医妇科健康状态问诊表", "templateId": 2014520536600776706},
    {"name": "前列腺炎病史采集表", "templateId": 2014539678649257986}
]

external_user_id = "test123"

# 测试函数
def test_scale_detail():
    for scale in scale_templates:
        print(f"\n=== 测试量表: {scale['name']} ===")
        
        # 1. 开始量表，获取recordId
        start_url = "http://127.0.0.1:8010/api/questionnaires/start"
        start_data = {
            "externalUserId": external_user_id,
            "templateId": scale["templateId"]
        }
        
        response = requests.post(start_url, json=start_data)
        if response.status_code != 200:
            print(f"  开始量表失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            continue
        
        start_result = response.json()
        record_id = start_result.get('recordId')
        if not record_id:
            print(f"  未获取到recordId: {start_result}")
            continue
        
        print(f"  开始量表成功，recordId: {record_id}")
        
        # 2. 获取量表详情
        detail_url = f"http://127.0.0.1:8010/api/questionnaires/detail?recordId={record_id}"
        response = requests.get(detail_url)
        
        if response.status_code != 200:
            print(f"  获取详情失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            continue
        
        detail_result = response.json()
        print(f"  详情接口返回: {json.dumps(detail_result, ensure_ascii=False)[:500]}...")
        
        # 3. 输出详情信息
        # 直接从根级别获取questions，而不是从data字段
        questions = detail_result.get('questions', [])
        print(f"  成功获取题目，题目数量: {len(questions)}")
        
        if questions:
            print("  前3道题的题目标题:")
            for i, q in enumerate(questions[:3], 1):
                print(f"    {i}. {q.get('title')}")
            
            # 输出第一道题的选项
            first_question = questions[0]
            options = first_question.get('options', [])
            if options:
                print("  第一道题的选项内容:")
                for j, opt in enumerate(options, 1):
                    print(f"    {j}. {opt.get('label')}: {opt.get('score') or opt.get('value')}")
        else:
            print("  未获取到题目")

if __name__ == "__main__":
    test_scale_detail()
