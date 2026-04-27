from db import (
    get_questionnaire_options,
    start_questionnaire,
    get_questionnaire_detail,
    submit_questionnaire,
    get_questionnaire_report,
    save_ai_reply,
    get_ai_reply,
    save_tongue_report,
    get_tongue_report,
    save_appointment_reminder,
    get_appointment_reminder,
    use_mysql
)
import uuid

def test_questionnaire_functions():
    print("测试问卷相关功能...")
    try:
        # 测试获取问卷选项
        options = get_questionnaire_options("test_user")
        print(f"获取问卷选项成功，模板数量: {len(options['scales'])}")
        
        # 测试开始问卷
        if options['scales']:
            template_id = options['scales'][0]['templateId']
            record_id = start_questionnaire("test_user", template_id)
            print(f"开始问卷成功，record_id: {record_id}")
            
            # 测试获取问卷详情
            detail = get_questionnaire_detail(record_id)
            print(f"获取问卷详情成功，题目数量: {len(detail['questions'])}")
            
            # 测试提交问卷
            answers = []
            for q in detail['questions']:
                answers.append({
                    'subjectId': q['subjectId'],
                    'value': '1'  # 简单测试值
                })
            submit_result = submit_questionnaire(record_id, answers)
            print(f"提交问卷成功，totalScore: {submit_result['totalScore']}")
            
            # 测试获取问卷报告
            report = get_questionnaire_report(record_id)
            print(f"获取问卷报告成功，status: {report['status']}")
        
        return True
    except Exception as e:
        print(f"问卷功能测试失败: {e}")
        return False

def test_ai_reply_functions():
    print("\n测试AI回复相关功能...")
    try:
        # 测试保存AI回复
        reply_id = str(uuid.uuid4())
        save_ai_reply(
            reply_id=reply_id,
            user_id="test_user",
            openid="test_openid",
            assistant_id="xiaohui",
            question="测试问题",
            content="测试回答",
            chat_id="test_chat"
        )
        print("保存AI回复成功")
        
        # 测试获取AI回复
        reply = get_ai_reply(reply_id)
        print(f"获取AI回复成功，question: {reply['question']}")
        
        return True
    except Exception as e:
        print(f"AI回复功能测试失败: {e}")
        return False

def test_tongue_report_functions():
    print("\n测试舌诊报告相关功能...")
    try:
        # 测试保存舌诊报告
        analysis_id = str(uuid.uuid4())
        save_tongue_report(
            analysis_id=analysis_id,
            user_id="test_user",
            openid="test_openid",
            report={"test": "report"},
            tips="测试提示"
        )
        print("保存舌诊报告成功")
        
        # 测试获取舌诊报告
        report = get_tongue_report(analysis_id)
        print(f"获取舌诊报告成功，analysis_id: {report['analysis_id']}")
        
        return True
    except Exception as e:
        print(f"舌诊报告功能测试失败: {e}")
        return False

def test_appointment_functions():
    print("\n测试预约提醒相关功能...")
    try:
        # 测试保存预约提醒
        appointment_id = str(uuid.uuid4())
        save_appointment_reminder(
            appointment_id=appointment_id,
            user_id="test_user",
            openid="test_openid",
            doctor_name="测试医生",
            clinic_time="2026-04-21 10:00:00",
            clinic_location="测试地点",
            remark="测试备注",
            status="待就诊"
        )
        print("保存预约提醒成功")
        
        # 测试获取预约提醒
        appointment = get_appointment_reminder(appointment_id)
        print(f"获取预约提醒成功，doctor_name: {appointment['doctor_name']}")
        
        return True
    except Exception as e:
        print(f"预约提醒功能测试失败: {e}")
        return False

def main():
    print(f"当前数据库类型: {'MySQL' if use_mysql() else 'SQLite'}")
    
    tests = [
        test_questionnaire_functions,
        test_ai_reply_functions,
        test_tongue_report_functions,
        test_appointment_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n测试结果: {passed}/{total} 测试通过")

if __name__ == "__main__":
    main()