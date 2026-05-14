-- 为 user_subscribe_reminder 表添加舌苔提醒自定义频率和时间字段
-- 执行时间: 2026-05-14

-- 1. 添加提醒间隔天数（默认每天）
ALTER TABLE user_subscribe_reminder
ADD COLUMN reminder_interval_days INT NOT NULL DEFAULT 1 COMMENT '几天提醒一次（1=每天,2=每两天,3=每三天,7=每周）';

-- 2. 提醒时间（已有此字段，确认格式为 HH:mm）
-- ALTER TABLE user_subscribe_reminder MODIFY COLUMN reminder_time VARCHAR(5) NOT NULL DEFAULT '08:00' COMMENT '提醒时间 HH:mm';

-- 3. 添加下次发送时间（用于定时任务判断）
ALTER TABLE user_subscribe_reminder
ADD COLUMN next_send_at DATETIME NULL COMMENT '下次应发送时间';

-- 4. 添加上次发送精确时间（补充 last_sent_date 的精度）
ALTER TABLE user_subscribe_reminder
ADD COLUMN last_sent_at DATETIME NULL COMMENT '上次实际发送时间';

-- 5. 添加索引优化查询性能
ALTER TABLE user_subscribe_reminder
ADD INDEX idx_next_send_at (next_send_at, enabled);

-- 验证字段是否添加成功
SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'user_subscribe_reminder'
AND COLUMN_NAME IN ('reminder_interval_days', 'reminder_time', 'next_send_at', 'last_sent_at')
ORDER BY ORDINAL_POSITION;
