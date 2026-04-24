import { AssistantId, requestAssistantReply } from '../../utils/util'
import { handleSubscribeAuthorization } from '../../utils/subscribe'

type ChatRole = 'assistant' | 'user'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  label: string
}

type CommonQuestion = {
  id: string
  text: string
}

type AssistantProfile = {
  id: AssistantId
  name: string
  introTitle: string
  introSubtitle: string
  introDescription: string
  greeting: string
  tags: string[]
  commonQuestions: string[]
  placeholder: string
  avatar: string
  avatarText: string
}

const assistantProfiles: Record<AssistantId, AssistantProfile> = {
  xiaohui: {
    id: 'xiaohui',
    name: '小慧',
    introTitle: '小慧智能体',
    introSubtitle: '妇科专注型 AI 助手',
    introDescription: '可咨询妇科常见问题、健康评估、备孕指导、复诊准备与服务流程相关问题。',
    greeting: '您好，我是小慧智能体，主要提供妇科相关的日常咨询、健康评估解读和复诊准备建议。',
    tags: ['妇科咨询', '备孕指导', '健康评估'],
    commonQuestions: [
      '月经不规律需要先做什么检查？',
      '备孕前需要提前准备哪些事项？',
      '白带异常应该先观察哪些情况？',
      '妇科复诊前要带哪些资料？'
    ],
    placeholder: '请输入您想咨询的妇科问题',
    avatar: '/assets/xiaohui.jpg',
    avatarText: '慧'
  },
  chen: {
    id: 'chen',
    name: '陈主任',
    introTitle: '陈主任智能体',
    introSubtitle: '男科专注型 AI 助手',
    introDescription: '可咨询男科门诊安排、健康评估、报告理解、复诊准备与连续随访相关问题。',
    greeting: '您好，我是陈主任智能体，主要提供男科门诊安排、健康评估解读和复诊准备相关问答。',
    tags: ['男科咨询', '门诊服务', '持续随访'],
    commonQuestions: [
      '如何预约陈主任门诊？',
      '复诊前需要准备哪些资料？',
      '评估结果出来后怎么理解？',
      '门诊后如何持续随访？'
    ],
    placeholder: '请输入您想咨询的男科问题',
    avatar: '/assets/chen.jpg',
    avatarText: '陈'
  }
}

function isAssistantId(value: string | undefined): value is AssistantId {
  return value === 'xiaohui' || value === 'chen'
}

function createAssistantMessage(id: string, content: string, label: string): ChatMessage {
  return {
    id,
    role: 'assistant',
    content,
    label
  }
}

function createUserMessage(id: string, content: string): ChatMessage {
  return {
    id,
    role: 'user',
    content,
    label: '我'
  }
}

function buildCommonQuestions(assistantId: AssistantId): CommonQuestion[] {
  return assistantProfiles[assistantId].commonQuestions.map((text, index) => ({
    id: `${assistantId}-${index + 1}`,
    text
  }))
}

function buildDefaultMessages(assistantId: AssistantId) {
  const assistant = assistantProfiles[assistantId]

  return [
    createAssistantMessage('msg-welcome', assistant.greeting, assistant.introTitle)
  ]
}

function buildPageState(assistantId: AssistantId) {
  const assistant = assistantProfiles[assistantId]

  return {
    currentAssistantId: assistantId,
    currentAssistant: assistant,
    profileTags: assistant.tags,
    commonQuestions: buildCommonQuestions(assistantId),
    messages: buildDefaultMessages(assistantId) as ChatMessage[],
    inputValue: '',
    canSend: false,
    isSending: false,
    chatId: '',
    scrollIntoView: 'msg-welcome'
  }
}

Page({
  data: {
    ...buildPageState('chen'),
    openid: ''
  },
  onLoad(query: Record<string, string | undefined>) {
    const assistantId = isAssistantId(query.assistantId) ? query.assistantId : 'chen'
    const presetQuestion = decodeURIComponent(query.presetQuestion || '').trim()
    const assistant = assistantProfiles[assistantId]

    wx.setNavigationBarTitle({
      title: assistant.introTitle
    })

    this.setData(buildPageState(assistantId))

    if (!presetQuestion) {
      return
    }

    void this.submitQuestion(presetQuestion)
  },
  onInputChange(event: WechatMiniprogram.CustomEvent) {
    const inputValue = event.detail.value as string

    this.setData({
      inputValue,
      canSend: Boolean(inputValue.trim())
    })
  },
  onTapCommonQuestion(event: WechatMiniprogram.CustomEvent) {
    if (this.data.isSending) {
      return
    }

    const question = event.currentTarget.dataset.question as string

    if (!question) {
      return
    }

    void this.submitQuestion(question)
  },
  onSendMessage() {
    if (!this.data.canSend || this.data.isSending) {
      return
    }

    const question = this.data.inputValue.trim()

    if (!question) {
      return
    }

    void this.submitQuestion(question)
  },
  async submitQuestion(question: string) {
    const assistantId = this.data.currentAssistantId as AssistantId
    const assistant = assistantProfiles[assistantId]
    const timestamp = Date.now()
    const userMessage = createUserMessage(`msg-user-${timestamp}`, question)
    const messages = [...this.data.messages, userMessage]

    this.setData({
      messages,
      inputValue: '',
      canSend: false,
      isSending: true,
      scrollIntoView: userMessage.id
    })

    try {
      const response = await requestAssistantReply({
        assistantId,
        question,
        chatId: this.data.chatId || undefined
      })
      const assistantMessage = createAssistantMessage(
        `msg-assistant-${Date.now()}`,
        response.content,
        assistant.introTitle
      )

      this.setData({
        messages: [...this.data.messages, assistantMessage],
        chatId: response.chatId || this.data.chatId,
        scrollIntoView: assistantMessage.id
      })
    } catch (error) {
      const errorMessage = createAssistantMessage(
        `msg-assistant-error-${Date.now()}`,
        error instanceof Error ? error.message : '服务暂时不可用，请稍后重试。',
        assistant.introTitle
      )

      this.setData({
        messages: [...this.data.messages, errorMessage],
        scrollIntoView: errorMessage.id
      })
    } finally {
      this.setData({
        isSending: false
      })
    }
  },
  async onSubscribeReminder() {
    const openid = this.data.openid
    
    if (!openid) {
      wx.showModal({
        title: '提示',
        content: '请先登录后再开启消息提醒',
        showCancel: false
      })
      return
    }

    await handleSubscribeAuthorization(openid, ['ai_reply'])
  },

})
