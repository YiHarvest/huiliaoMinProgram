export type ExpertProfile = {
  id: string
  name: string
  title: string
  department: string
  focus: string[]
  summary: string
  serviceLabel: string
  theme: 'teal' | 'cyan' | 'mint' | 'gold'
}

export const expertProfiles: ExpertProfile[] = [
  {
    id: 'wang-lan',
    name: '王兰',
    title: '主任医师',
    department: '中医内科',
    focus: ['慢病调理', '体质辨识'],
    summary: '聚焦慢病管理与体质调理，适合长期健康管理与评估指导。',
    serviceLabel: '查看服务',
    theme: 'teal'
  },
  {
    id: 'liu-yan',
    name: '刘妍',
    title: '副主任医师',
    department: '中西医结合',
    focus: ['舌诊辨证', '睡眠调理'],
    summary: '擅长结合舌诊结果与问诊信息，提供个体化调养建议。',
    serviceLabel: '查看服务',
    theme: 'cyan'
  },
  {
    id: 'chen-jun',
    name: '陈骏',
    title: '主任医师',
    department: '专家门诊',
    focus: ['门诊随访', '专病管理'],
    summary: '适合需要专家门诊指导、长期随访与复诊衔接的患者。',
    serviceLabel: '查看服务',
    theme: 'mint'
  },
  {
    id: 'zhao-qing',
    name: '赵青',
    title: '特聘专家',
    department: '健康管理',
    focus: ['风险评估', '康复指导'],
    summary: '提供健康风险评估、康复阶段建议与长期干预方向判断。',
    serviceLabel: '查看服务',
    theme: 'gold'
  }
]
