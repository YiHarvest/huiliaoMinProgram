export type ExpertProfile = {
  id: string
  name: string
  title: string
  department: string
  focus: string[]
  summary: string
  serviceLabel: string
  theme: 'teal' | 'cyan' | 'mint' | 'gold'
  schedule?: string
  details?: {
    intro: string
    honors: string
    expertise: string
    schedule: {
      monday: string
      tuesday: string
      wednesday: string
      thursday: string
      friday: string
      saturday: string
      sunday: string
    }
  }
}

export const expertProfiles: ExpertProfile[] = [
  {
    id: 'chen-wangqiang',
    name: '陈望强',
    title: '主任中医师',
    department: '生殖医学科男科',
    focus: ['前列腺疾病', '男科疾病'],
    summary: '基于"前列腺结构分型理论"和"前列腺炎络病理论"，形成"慢性前列腺炎症因理论"，创立"前列腺炎导浊疗法"。',
    serviceLabel: '查看服务',
    theme: 'gold',
    schedule: '周二、周日全天，周三、四、五上午',
    details: {
      intro: '陈望强主任中医师,是杭州市红十字会医院生殖医学科男科主任,研究生导师,毕业于北京中医药大学男科学专业,师从李海松教授。国家级名中医鲍严钟学术继承人。',
      honors: '2021年荣获杭州市"最美医生"称号,并被评为中青年中医骨干、医院青年中医人才。现任中华中医药学会男科分会委员,中华中医药学会生殖医学分会委员,中国性学会中西医结合生殖医学分会常委,杭州市中西医结合学会生殖专委会副主任委员等。',
      expertise: '陈望强主任有15年男科临床经验,基于鲍严钟的"前列腺结构分型理论"之上,汲取导师李海松教授的"前列腺炎络病理论"经验,并结合自身临床经验总结,通过逾12万人次的临床实践,逐渐形成"慢性前列腺炎症因理论",并基于此理论拟定出一套疗效好,操作方便的"前列腺炎导浊疗法",临床疗效反馈良好,针对诸多顽固性慢性前列腺炎病例,该疗法展现出显著成效,因而吸引了众多外地患者前来寻求治疗。',
      schedule: {
        monday: '不出诊',
        tuesday: '上午(8点到12点)红会医院仁爱院区门诊2楼男科门诊，下午(1点30到5点)红会医院仁爱院区门诊2楼男科门诊',
        wednesday: '上午(8点到12点)红会医院钱塘院区(原第九人民医院)生殖医学科男性疾病特需门诊，不出诊',
        thursday: '上午(8点到12点)红会医院仁爱院区门诊2楼男科门诊，不出诊',
        friday: '上午(8点到12点)红会医院仁爱院区门诊2楼男科门诊，不出诊',
        saturday: '不出诊',
        sunday: '上午(8点到12点)红会医院仁爱院区门诊2楼男科门诊，下午(1点30到5点)红会医院仁爱院区门诊2楼男科门诊'
      }
    }
  },
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
