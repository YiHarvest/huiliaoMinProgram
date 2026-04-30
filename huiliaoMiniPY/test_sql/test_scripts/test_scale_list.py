import json
import requests

# 测试量表列表接口
url = "http://127.0.0.1:8010/api/questionnaires/options?externalUserId=test123"

response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    
    # 统计信息
    categories = data.get('categories', [])
    scales = data.get('scales', [])
    
    print(f"量表总数: {len(scales)}")
    print(f"分类总数: {len(categories)}")
    print("\n前20个量表名称:")
    for i, scale in enumerate(scales[:20], 1):
        print(f"{i}. {scale.get('questionnaireName')}")
    
    # 检查特定量表
    print("\n重点检查的量表:")
    target_scales = [
        "男性不育病史采集表",
        "国际勃起功能评分5项（IIEF-5）",
        "前列腺炎病史采集表",
        "妇科相关量表",
        "失眠程度自评量表"
    ]
    
    for target in target_scales:
        found = False
        for scale in scales:
            if target in scale.get('questionnaireName', ''):
                found = True
                print(f"找到: {scale.get('questionnaireName')}")
                break
        if not found:
            print(f"未找到: {target}")
    
    # 输出前5个量表的templateId，用于测试详情接口
    print("\n前5个量表的templateId:")
    for i, scale in enumerate(scales[:5], 1):
        print(f"{i}. {scale.get('questionnaireName')}: {scale.get('templateId')}")
    
    # 保存完整数据到文件
    with open('scale_list.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n完整数据已保存到 scale_list.json")
else:
    print(f"请求失败: {response.status_code}")
    print(f"错误信息: {response.text}")
