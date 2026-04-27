import json

# 测试大整数的 JSON 序列化
large_id = 2044969684322750465
print(f"原始整数: {large_id}")
print(f"原始整数类型: {type(large_id)}")

# 序列化为 JSON
json_str = json.dumps({'templateId': large_id})
print(f"JSON 字符串: {json_str}")

# 序列化为 JSON，将整数转换为字符串
json_str_str = json.dumps({'templateId': str(large_id)})
print(f"JSON 字符串（字符串类型）: {json_str_str}")

# 模拟 JavaScript 解析
import js2py

# 解析数字类型
js_code = f"var data = {json_str}; data.templateId"
try:
    js_result = js2py.eval_js(js_code)
    print(f"JavaScript 解析数字: {js_result}")
    print(f"JavaScript 解析数字与原始值是否相等: {js_result == large_id}")
except Exception as e:
    print(f"JavaScript 解析数字错误: {e}")

# 解析字符串类型
js_code_str = f"var data = {json_str_str}; data.templateId"
try:
    js_result_str = js2py.eval_js(js_code_str)
    print(f"JavaScript 解析字符串: {js_result_str}")
    print(f"JavaScript 解析字符串与原始值是否相等: {int(js_result_str) == large_id}")
except Exception as e:
    print(f"JavaScript 解析字符串错误: {e}")
