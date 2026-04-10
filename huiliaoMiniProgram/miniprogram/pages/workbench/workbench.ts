import { expertProfiles } from '../../data/experts'

type AssistantId = 'xiaohui' | 'chen'

type AssistantProfile = {
  id: AssistantId
  name: string
  role: string
  summary: string
  description: string
  tags: string[]
  accent: 'xiaohui' | 'chen'
  avatar: string
  status: string
}

type ServiceItem = {
  key: string
  title: string
  desc: string
  iconText: string
  theme: string
  action: 'toast' | 'experts' | 'tongue-upload' | 'assistant-chat'
}

type RecentServiceItem = {
  key: string
  title: string
  time: string
  status: string
  actionText: string
}

const assistants: Record<AssistantId, AssistantProfile> = {
  xiaohui: {
    id: 'xiaohui',
    name: '小慧',
    role: 'AI 健康助理',
    summary: '面向女性日常咨询与健康服务陪伴',
    description: '小慧主要聚焦妇科场景，适合承接月经、白带、备孕、复诊准备、报告理解与基础分诊引导。',
    tags: ['妇科咨询', '备孕指导', '健康评估'],
    accent: 'xiaohui',
    avatar: '/assets/xiaohui.jpg',
    status: '当前服务中'
  },
  chen: {
    id: 'chen',
    name: '陈主任',
    role: '专家门诊助手',
    summary: '面向男科门诊服务、预约衔接与复诊指导',
    description: '陈主任主要聚焦男科场景，适合处理预约挂号、诊前准备、评估结果辅助理解与诊后随访问题。',
    tags: ['男科咨询', '门诊服务', '持续随访'],
    accent: 'chen',
    avatar: '/assets/chen.jpg',
    status: '可切换使用'
  }
}

const questionSuggestions: Record<AssistantId, string[]> = {
  xiaohui: [
    '月经不规律需要先做什么检查？',
    '备孕前需要提前准备哪些事项？',
    '白带异常应该先观察哪些情况？',
    '妇科复诊前要带哪些资料？'
  ],
  chen: [
    '如何预约陈主任门诊？',
    '复诊前需要准备哪些资料？',
    '评估结果出来后怎么理解？',
    '门诊后如何持续随访？'
  ]
}

const serviceCatalog: Record<AssistantId, ServiceItem[]> = {
  xiaohui: [
    { key: 'qa', title: '在线问答', desc: '快速发起妇科相关提问', iconText: '问', theme: 'teal', action: 'assistant-chat' },
    { key: 'assessment', title: '健康评估', desc: '查看评估入口与报告', iconText: '评', theme: 'mint', action: 'toast' },
    { key: 'tongue', title: '舌诊入口', desc: '进入舌诊识别流程', iconText: '舌', theme: 'cyan', action: 'tongue-upload' },
    { key: 'doctor', title: '了解医生', desc: '查看合作医生与方向', iconText: '医', theme: 'gold', action: 'experts' },
    { key: 'reminder', title: '服务提醒', desc: '订阅结果和随访通知', iconText: '提', theme: 'teal', action: 'toast' },
    { key: 'wechat', title: '加企业微信', desc: '连接专属服务入口', iconText: '微', theme: 'cyan', action: 'toast' }
  ],
  chen: [
    { key: 'qa', title: '在线问答', desc: '整理男科门诊核心问题', iconText: '问', theme: 'teal', action: 'assistant-chat' },
    { key: 'booking', title: '预约挂号', desc: '衔接专家门诊预约', iconText: '约', theme: 'gold', action: 'toast' },
    { key: 'assessment', title: '健康评估', desc: '辅助理解当前结果', iconText: '评', theme: 'mint', action: 'toast' },
    { key: 'tongue', title: '舌诊入口', desc: '结合辨证信息查看', iconText: '舌', theme: 'cyan', action: 'tongue-upload' },
    { key: 'reminder', title: '服务提醒', desc: '订阅随访和复诊通知', iconText: '提', theme: 'teal', action: 'toast' },
    { key: 'wechat', title: '加企业微信', desc: '连接门诊服务通道', iconText: '微', theme: 'cyan', action: 'toast' }
  ]
}

const recentServicesByAssistant: Record<AssistantId, RecentServiceItem[]> = {
  xiaohui: [
    { key: 'recent-assessment', title: '最近评估', time: '今天 09:40', status: '结果待查看', actionText: '查看结果' },
    { key: 'recent-tongue', title: '最近舌诊', time: '昨天 18:20', status: '已生成建议', actionText: '查看详情' },
    { key: 'recent-reminder', title: '最近提醒', time: '04-07 15:30', status: '已订阅成功', actionText: '查看设置' }
  ],
  chen: [
    { key: 'recent-booking', title: '最近预约', time: '今天 10:15', status: '待确认排班', actionText: '查看详情' },
    { key: 'recent-assessment', title: '最近评估', time: '昨天 17:10', status: '已同步门诊', actionText: '查看结果' },
    { key: 'recent-followup', title: '最近随访', time: '04-08 11:20', status: '问卷待填写', actionText: '继续填写' }
  ]
}

function navigateToAssistantChat(assistantId: AssistantId, presetQuestion?: string) {
  const question = presetQuestion ? presetQuestion.trim() : undefined
  const baseUrl = `/pages/chen-agent/chen-agent?assistantId=${assistantId}`

  if (question) {
    wx.navigateTo({
      url: `${baseUrl}&presetQuestion=${encodeURIComponent(question)}`
    })
    return
  }

  wx.navigateTo({
    url: baseUrl
  })
}

function buildWorkbenchState(assistantId: AssistantId) {
  return {
    currentAssistantId: assistantId,
    currentAssistant: assistants[assistantId],
    recommendedAssistantName: assistants[assistantId].name,
    serviceGrid: serviceCatalog[assistantId],
    questionSuggestions: questionSuggestions[assistantId],
    recentServices: recentServicesByAssistant[assistantId]
  }
}

Component({
  data: {
    serviceTarget: '本人',
    qaDraft: '',
    assistants: Object.values(assistants),
    previewExperts: expertProfiles.slice(0, 3),
    ...buildWorkbenchState('xiaohui')
  },
  methods: {
    onServiceTargetTap() {
      wx.showToast({
        title: '家庭成员功能待开放',
        icon: 'none'
      })
    },
    onSelectAssistant(event: WechatMiniprogram.CustomEvent) {
      const assistantId = event.currentTarget.dataset.id as AssistantId

      if (!assistantId || assistantId === this.data.currentAssistantId) {
        return
      }

      this.setData({
        qaDraft: '',
        ...buildWorkbenchState(assistantId)
      })
    },
    onMoreAssistants() {
      wx.showToast({
        title: '更多助手功能待开放',
        icon: 'none'
      })
    },
    onTapService(event: WechatMiniprogram.CustomEvent) {
      const { title, action } = event.currentTarget.dataset as {
        title: string
        action: 'toast' | 'experts' | 'tongue-upload' | 'assistant-chat'
      }

      if (action === 'experts') {
        wx.navigateTo({
          url: '/pages/experts/experts'
        })
        return
      }

      if (action === 'tongue-upload') {
        wx.navigateTo({
          url: '/pages/tongue-upload/tongue-upload'
        })
        return
      }

      if (action === 'assistant-chat') {
        navigateToAssistantChat(this.data.currentAssistantId)
        return
      }

      wx.showToast({
        title: `${title}功能待接入`,
        icon: 'none'
      })
    },
    onSelectQuestion(event: WechatMiniprogram.CustomEvent) {
      const question = event.currentTarget.dataset.question as string
      navigateToAssistantChat(this.data.currentAssistantId, question)
    },
    onQaInput(event: WechatMiniprogram.CustomEvent) {
      this.setData({
        qaDraft: event.detail.value
      })
    },
    onSendQa() {
      const question = this.data.qaDraft.trim()

      if (!question) {
        return
      }

      this.setData({
        qaDraft: ''
      })

      navigateToAssistantChat(this.data.currentAssistantId, question)
    },
    onViewRecentService(event: WechatMiniprogram.CustomEvent) {
      const title = event.currentTarget.dataset.title as string

      wx.showToast({
        title: `${title}详情待接入`,
        icon: 'none'
      })
    },
    onSubscribeReminder() {
      wx.showToast({
        title: '订阅提醒功能待接入',
        icon: 'none'
      })
    },
    onOpenExperts() {
      wx.navigateTo({
        url: '/pages/experts/experts'
      })
    }
  }
})
