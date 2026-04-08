export type ModeArticleSection = {
  title: string
  paragraphs: string[]
}

export type ModeArticle = {
  id: string
  cardTitle: string
  cardSummary: string
  cardTag: string
  title: string
  lead: string
  coverImage: string
  sections: ModeArticleSection[]
}

export const modeArticles: ModeArticle[] = [
  {
    id: 'hospital-system',
    cardTag: '体系接入',
    cardTitle: '如何接入医院官方体系',
    cardSummary: '围绕公众号、互联网医院与诊疗闭环完成体系接入。',
    title: '如何接入医院官方体系',
    lead: '这篇内容回答榕慧模式如何嵌入医院体系，确保专家服务不是外置工具，而是与门诊、科普、咨询等真实业务场景协同运转。',
    coverImage: '/assets/home-banner-hero-cropped.png',
    sections: [
      {
        title: '背景问题',
        paragraphs: [
          '很多数字化服务之所以难长期运行，不是因为功能不够，而是没有进入医院官方体系。',
          '如果用户需要在公众号、挂号、咨询、支付和处方之外再跳转到另一套体系，信任感、转化率和持续使用率都会受到影响。'
        ]
      },
      {
        title: '核心思路',
        paragraphs: [
          '榕慧模式不是把服务独立挂在医院体系之外，而是围绕公众号、互联网医院和诊疗闭环做一体化接入。',
          '这样用户感知到的是医院连续服务的一部分，而不是额外安装的一套新工具。'
        ]
      },
      {
        title: '落地路径',
        paragraphs: [
          '第一步是围绕门诊、科普、咨询等真实业务场景梳理服务入口，明确用户触达路径。',
          '第二步是把挂号、支付、处方、随访等关键节点串联起来，形成稳定闭环。',
          '第三步是在医院官方触点中嵌入 AI 辅助能力，让服务延伸但不割裂。'
        ]
      },
      {
        title: '结果价值',
        paragraphs: [
          '接入官方体系后，专家服务更容易获得患者信任，也更方便形成长期运营基础。',
          '同时，医院侧可以保留服务主场，专家侧可以获得更稳定的数字化能力承接。'
        ]
      },
      {
        title: '总结',
        paragraphs: [
          '接入医院体系的重点，不是单点功能接进去，而是把专家服务放回医院已有业务逻辑中。',
          '这也是榕慧模式能够长期落地的第一步。'
        ]
      }
    ]
  },
  {
    id: 'patient-pool',
    cardTag: '患者沉淀',
    cardTitle: '如何构建私域患者池',
    cardSummary: '通过量表、随访、科普和持续服务沉淀患者关系。',
    title: '如何构建私域患者池',
    lead: '这篇内容回答患者关系为什么不能只停留在单次问诊，以及榕慧模式如何把触达、教育和随访变成可持续连接。',
    coverImage: '/assets/home-banner-hero-cropped.png',
    sections: [
      {
        title: '背景问题',
        paragraphs: [
          '单次门诊可以解决当下问题，但很难支撑长期健康管理和持续服务。',
          '如果缺少后续触达机制，患者关系就会停留在一次性诊疗，难以形成复访、教育和长期陪伴。'
        ]
      },
      {
        title: '核心思路',
        paragraphs: [
          '榕慧模式把患者沉淀理解为持续连接，而不是简单拉群或增加通讯录。',
          '内容、量表、随访和健康科普共同构成患者关系的维护机制。'
        ]
      },
      {
        title: '落地路径',
        paragraphs: [
          '先通过门诊后触达和专题内容建立初始连接，让患者愿意进入持续服务场景。',
          '再通过量表评估、定期随访和健康教育把连接转化为有节奏的互动。',
          '最后把不同触点沉淀成可运营的患者池，为后续服务和分析提供基础。'
        ]
      },
      {
        title: '结果价值',
        paragraphs: [
          '患者池建立后，专家服务不再依赖单次门诊，而是拥有持续触达和陪伴的能力。',
          '这不仅能提升患者体验，也能为长期运营提供更稳定的数据和关系基础。'
        ]
      },
      {
        title: '总结',
        paragraphs: [
          '私域患者池的价值不在数量，而在能否形成稳定、高质量的持续连接。',
          '榕慧模式强调的是把患者关系沉淀成长期服务资产。'
        ]
      }
    ]
  },
  {
    id: 'long-term-operation',
    cardTag: '长期运营',
    cardTitle: '如何形成长期数字化服务能力',
    cardSummary: '把知识库、患者陪伴和数据分析组合成长期运营能力。',
    title: '如何形成长期数字化服务能力',
    lead: '这篇内容回答为什么很多项目只能短期上线、无法长期运转，以及榕慧模式如何用 AI 和数据帮助专家建立稳定服务能力。',
    coverImage: '/assets/home-banner-hero-cropped.png',
    sections: [
      {
        title: '背景问题',
        paragraphs: [
          '数字化工具上线并不等于拥有数字化服务能力，很多项目的问题在于只能完成展示，不能形成长期运营。',
          '如果没有知识沉淀、患者陪伴和数据反馈，服务就很难持续迭代。'
        ]
      },
      {
        title: '核心思路',
        paragraphs: [
          '榕慧模式把长期能力拆成三件事：知识库沉淀、全周期患者陪伴、数据结果分析。',
          '这三部分共同作用，才能让专家服务真正从单次动作变成长期运营体系。'
        ]
      },
      {
        title: '落地路径',
        paragraphs: [
          '先把专家经验、方案和内容沉淀为可复用知识资产，形成服务底座。',
          '再用 AI 和自动化机制承接患者全周期服务，降低人工重复成本。',
          '最后通过数据分析回看服务结果，让后续运营和内容策略持续优化。'
        ]
      },
      {
        title: '结果价值',
        paragraphs: [
          '长期数字化服务能力建立后，专家可以更稳定地输出服务，也更容易沉淀个人方法论。',
          '平台侧则能从结果中持续优化策略，而不是依赖一次次重新搭建。'
        ]
      },
      {
        title: '总结',
        paragraphs: [
          '长期能力不是某一个功能点，而是一套可持续运行的方法论。',
          '这也是榕慧模式区别于短期项目型方案的关键。'
        ]
      }
    ]
  }
]

export const modeArticleMap = modeArticles.reduce<Record<string, ModeArticle>>((acc, article) => {
  acc[article.id] = article
  return acc
}, {})
