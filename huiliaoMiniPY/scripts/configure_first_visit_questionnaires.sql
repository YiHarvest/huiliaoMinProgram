-- ====================================================================
-- 脚本名称: configure_first_visit_questionnaires.sql
-- 功能: 配置首诊必填问卷
-- 说明: 将指定的问卷标记为首诊必填 (visit_stage = 'first_only')
-- 注意: 执行前请备份数据库！
-- ====================================================================

USE miniprogramYQY;

-- ====================================================================
-- 第一步：查看当前的医生-问卷绑定配置
-- ====================================================================
-- SELECT b.id, b.doctor_id, d.doctor_name, b.questionnaire_id, qt.questionnaire_name, 
--        b.visit_stage, b.sort_order, b.status
-- FROM doctor_questionnaire_bind b
-- JOIN doctor_profile d ON d.id = b.doctor_id
-- JOIN crm_questionnaire_template qt ON qt.id = b.questionnaire_id
-- WHERE b.status = 1 AND d.status = 1
-- ORDER BY b.doctor_id, b.sort_order;

-- ====================================================================
-- 第二步：配置首诊必填问卷
-- 
-- 根据问卷名称，识别哪些是首诊必填的问卷，将其 visit_stage 更新为 'first_only'
-- ====================================================================

-- 方案A: 按问卷名称匹配（推荐）
-- 这些问卷名称通常包含"第一次填表"、"初诊"、"首诊"等关键词
UPDATE doctor_questionnaire_bind b
SET b.visit_stage = 'first_only'
WHERE b.status = 1
  AND b.questionnaire_id IN (
    SELECT id FROM crm_questionnaire_template
    WHERE (questionnaire_name LIKE '%第一次填表%'
       OR questionnaire_name LIKE '%初诊%'
       OR questionnaire_name LIKE '%首诊%'
       OR questionnaire_name LIKE '%初筛%')
    AND (del_flag = '0' OR del_flag IS NULL)
  );

-- ====================================================================
-- 第三步：验证配置结果
-- ====================================================================
SELECT 
    b.id,
    d.id as doctor_id,
    d.doctor_name,
    qt.id as questionnaire_id,
    qt.questionnaire_name,
    b.visit_stage,
    b.sort_order
FROM doctor_questionnaire_bind b
JOIN doctor_profile d ON d.id = b.doctor_id
JOIN crm_questionnaire_template qt ON qt.id = b.questionnaire_id
WHERE b.status = 1 
  AND d.status = 1
  AND b.visit_stage = 'first_only'
ORDER BY d.doctor_id, b.sort_order;

-- ====================================================================
-- 第四步：检查 patient_doctor_visit_state 表的初始状态
-- ====================================================================
-- 确保该表中患者与医生的记录状态正确
SELECT * FROM patient_doctor_visit_state
WHERE patient_id = ? AND doctor_id = ?
LIMIT 1;

-- 如果记录不存在或 first_visit_completed 为 1 且患者是首诊，需要重置：
-- UPDATE patient_doctor_visit_state
-- SET first_visit_completed = 0, first_visit_completed_at = NULL
-- WHERE patient_id = ? AND doctor_id = ?;

-- 或新增记录：
-- INSERT INTO patient_doctor_visit_state (patient_id, doctor_id, first_visit_completed)
-- VALUES (?, ?, 0)
-- ON DUPLICATE KEY UPDATE first_visit_completed = 0;
