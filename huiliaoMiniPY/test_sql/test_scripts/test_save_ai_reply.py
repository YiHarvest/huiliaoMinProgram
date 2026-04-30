from db import save_ai_reply
import uuid

print('测试 save_ai_reply 函数...')
try:
    # 尝试保存一个 AI 回复
    save_ai_reply(
        reply_id=uuid.uuid4().hex,
        user_id='test_user',
        openid='test_openid',
        assistant_id='xiaohui',
        question='测试问题',
        content='测试回复',
        chat_id=uuid.uuid4().hex
    )
    print('测试成功：save_ai_reply 函数没有抛出异常')
except Exception as e:
    print(f'测试失败：save_ai_reply 函数抛出异常: {e}')
