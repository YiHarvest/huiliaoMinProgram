CREATE TABLE IF NOT EXISTS questionnaire_record (
    record_id VARCHAR(64) PRIMARY KEY,
    questionnaire_id VARCHAR(64) NOT NULL,
    questionnaire_name VARCHAR(255) NOT NULL,
    doctor_id BIGINT NULL,
    patient_id BIGINT NULL,
    disease_type VARCHAR(64) NULL,
    visit_type VARCHAR(32) NULL,
    answers_json LONGTEXT NOT NULL,
    analysis_text LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_questionnaire_record_patient_created (patient_id, created_at),
    INDEX idx_questionnaire_record_doctor_created (doctor_id, created_at),
    INDEX idx_questionnaire_record_questionnaire (questionnaire_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
