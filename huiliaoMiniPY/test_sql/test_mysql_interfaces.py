import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql_storage import (
    get_questionnaire_options_mysql,
    start_questionnaire_mysql,
    get_questionnaire_detail_mysql,
    submit_questionnaire_mysql,
    get_questionnaire_report_mysql
)

def test_get_questionnaire_options():
    print("\n" + "=" * 80)
    print("Test 1: get_questionnaire_options_mysql")
    print("=" * 80)

    try:
        result = get_questionnaire_options_mysql('wmq5A1UwAAX-NAPLnBZPCnhDS3ELFOjw')
        print("[OK] Success")
        print("Return fields: " + str(list(result.keys())))
        print("Categories count: " + str(len(result.get('categories', []))))
        print("Scales count: " + str(len(result.get('scales', []))))

        if result.get('scales'):
            print("\nFirst scale example:")
            scale = result['scales'][0]
            for k, v in scale.items():
                print("  " + str(k) + ": " + str(v))

        return True, result
    except Exception as e:
        print("[FAIL] " + str(e))
        import traceback
        traceback.print_exc()
        return False, None


def test_start_questionnaire(template_id):
    print("\n" + "=" * 80)
    print("Test 2: start_questionnaire_mysql (template_id=" + str(template_id) + ")")
    print("=" * 80)

    try:
        record_id = start_questionnaire_mysql('test_user_123', template_id)
        print("[OK] Success")
        print("Return record_id: " + str(record_id))
        return True, record_id
    except Exception as e:
        print("[FAIL] " + str(e))
        import traceback
        traceback.print_exc()
        return False, None


def test_get_questionnaire_detail(record_id):
    print("\n" + "=" * 80)
    print("Test 3: get_questionnaire_detail_mysql (record_id=" + str(record_id) + ")")
    print("=" * 80)

    try:
        result = get_questionnaire_detail_mysql(record_id)
        print("[OK] Success")
        print("Return fields: " + str(list(result.keys())))
        print("Questionnaire name: " + str(result.get('questionnaireName')))
        print("Questions count: " + str(len(result.get('questions', []))))

        if result.get('questions'):
            print("\nFirst question example:")
            q = result['questions'][0]
            for k, v in q.items():
                if k != 'options':
                    print("  " + str(k) + ": " + str(v))
                else:
                    print("  " + str(k) + ": (" + str(len(v)) + " options)")

        return True, result
    except Exception as e:
        print("[FAIL] " + str(e))
        import traceback
        traceback.print_exc()
        return False, None


def test_submit_questionnaire(record_id, answers):
    print("\n" + "=" * 80)
    print("Test 4: submit_questionnaire_mysql (record_id=" + str(record_id) + ")")
    print("=" * 80)

    try:
        result = submit_questionnaire_mysql(record_id, answers)
        print("[OK] Success")
        print("Return fields: " + str(list(result.keys())))
        print("success: " + str(result.get('success')))
        print("recordId: " + str(result.get('recordId')))
        print("totalScore: " + str(result.get('totalScore')))
        return True, result
    except Exception as e:
        print("[FAIL] " + str(e))
        import traceback
        traceback.print_exc()
        return False, None


def test_get_questionnaire_report(record_id):
    print("\n" + "=" * 80)
    print("Test 5: get_questionnaire_report_mysql (record_id=" + str(record_id) + ")")
    print("=" * 80)

    try:
        result = get_questionnaire_report_mysql(record_id)
        print("[OK] Success")
        print("Return fields: " + str(list(result.keys())))
        for k, v in result.items():
            if k == 'answers':
                print("  " + str(k) + ": (" + str(len(v)) + " answers)")
            else:
                print("  " + str(k) + ": " + str(v))
        return True, result
    except Exception as e:
        print("[FAIL] " + str(e))
        import traceback
        traceback.print_exc()
        return False, None


def main():
    print("=" * 80)
    print("MySQL Questionnaire Interface Test")
    print("=" * 80)

    all_passed = True

    passed, options_result = test_get_questionnaire_options()
    all_passed = all_passed and passed

    if not options_result or not options_result.get('scales'):
        print("\n[ABORT] Cannot get scales list, stop testing")
        return False

    first_scale = options_result['scales'][0]
    template_id = first_scale['templateId']
    print("\nUsing first scale for testing: templateId=" + str(template_id) + ", name=" + first_scale['questionnaireName'])

    passed, record_id = test_start_questionnaire(template_id)
    all_passed = all_passed and passed

    if not record_id:
        print("\n[ABORT] Cannot start questionnaire, stop testing")
        return all_passed

    passed, detail_result = test_get_questionnaire_detail(record_id)
    all_passed = all_passed and passed

    if not detail_result or not detail_result.get('questions'):
        print("\n[WARN] Cannot get questionnaire detail (may have no questions)")
    else:
        questions = detail_result['questions'][:3]
        answers = []
        for q in questions:
            answers.append({
                'subjectId': q['subjectId'],
                'value': q['options'][0]['label'] if q.get('options') else 'Test Answer'
            })

        passed, _ = test_submit_questionnaire(record_id, answers)
        all_passed = all_passed and passed

        passed, _ = test_get_questionnaire_report(record_id)
        all_passed = all_passed and passed

    print("\n" + "=" * 80)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    main()