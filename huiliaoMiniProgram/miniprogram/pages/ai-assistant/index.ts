import { AssistantId, requestAssistantReply } from '../../utils/util'

type ChatRole = 'assistant' | 'user'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  label: string
  type?: 'text' | 'image' | 'file'
  mediaUrl?: string
  fileName?: string
  fileSize?: number
  fileSizeText?: string
}

type CommonQuestion = {
  id: string
  text: string
}

const questionPool = [
  '备孕前需要提前准备哪些事项？',
  '月经不规律需要先做什么检查？',
  '白带异常应该先观察哪些情况？',
  '男科备孕需要注意哪些事项？',
  '精液检查前需要注意什么？',
  '备孕期间同房频率怎么安排比较合适？',
  '检查报告里有异常指标应该怎么看？',
  '备孕期间需要补充哪些营养？',
  '排卵期怎么判断比较准确？',
  '男性长期熬夜会影响备孕吗？',
  '妇科炎症会影响备孕吗？',
  '备孕前夫妻双方需要做哪些检查？'
]

const GREETING = '您好，我是智能助手，可以为您提供妇科、男科、备孕、报告解读等相关健康咨询建议。请描述您的问题，我会尽量帮您分析。'

function createAssistantMessage(id: string, content: string, label: string): ChatMessage {
  return {
    id,
    role: 'assistant',
    content,
    label,
    type: 'text',
    isLoading: content === '正在思考中...'
  }
}

function createUserMessage(id: string, content: string, type?: 'text' | 'image' | 'file', mediaUrl?: string, fileName?: string, fileSize?: number, fileSizeText?: string): ChatMessage {
  return {
    id,
    role: 'user',
    content,
    label: '我',
    type: type || 'text',
    mediaUrl,
    fileName,
    fileSize,
    fileSizeText
  }
}

function shuffleArray<T>(array: T[]): T[] {
  const result = [...array]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

function getRandomQuestions(): CommonQuestion[] {
  const shuffled = shuffleArray(questionPool)
  return shuffled.slice(0, 4).map((text, index) => ({
    id: `question-${index + 1}`,
    text
  }))
}

interface ChatSession {
  id: string
  title: string
  preview: string
  updatedAt: string
  messages: ChatMessage[]
}

const STORAGE_KEY = 'AI_CHAT_SESSIONS'
const MAX_SESSIONS = 50

Page({
  data: {
    commonQuestions: getRandomQuestions() as CommonQuestion[],
    messages: [
      createAssistantMessage('msg-welcome', GREETING, '智能助手')
    ] as ChatMessage[],
    inputValue: '',
    canSend: false,
    isSending: false,
    chatId: '',
    scrollIntoView: 'msg-welcome',
    
    historyVisible: false,
    currentSessionId: '',
    chatSessions: [] as ChatSession[],
    statusBarHeight: 0,
    navBarHeight: 0,
    
    showAttachmentPanel: false
  },

  onLoad(): void {
    this.initNavBarHeight()
    this.loadChatSessions()
  },

  initNavBarHeight(): void {
    const systemInfo = wx.getSystemInfoSync()
    const menuButtonInfo = wx.getMenuButtonBoundingClientRect?.()
    
    const statusBarHeight = systemInfo.statusBarHeight || 0
    let navBarHeight = 44
    
    if (menuButtonInfo) {
      navBarHeight = menuButtonInfo.bottom - statusBarHeight + 8
    }
    
    this.setData({
      statusBarHeight,
      navBarHeight
    })
  },

  loadChatSessions(): void {
    try {
      const data = wx.getStorageSync(STORAGE_KEY)
      const sessions = data ? JSON.parse(data) : []
      this.setData({
        chatSessions: sessions
      })
      
      if (!this.data.currentSessionId && sessions.length > 0) {
        this.setData({
          currentSessionId: sessions[0].id
        })
      }
    } catch (error) {
      console.error('Load chat sessions failed:', error)
      this.setData({
        chatSessions: []
      })
    }
  },

  saveChatSessions(sessions: ChatSession[]): void {
    try {
      wx.setStorageSync(STORAGE_KEY, JSON.stringify(sessions))
    } catch (error) {
      console.error('Save chat sessions failed:', error)
    }
  },

  openHistoryDrawer(): void {
    this.loadChatSessions()
    this.setData({
      historyVisible: true
    })
  },

  closeHistoryDrawer(): void {
    this.setData({
      historyVisible: false
    })
  },

  createNewSession(): void {
    this.setData({
      messages: [createAssistantMessage('msg-welcome', GREETING, '智能助手')],
      currentSessionId: '',
      chatId: '',
      historyVisible: false,
      scrollIntoView: 'msg-welcome'
    })
  },

  switchSession(event: WechatMiniprogram.CustomEvent): void {
    const sessionId = event.currentTarget.dataset.sessionId as string
    const sessions = this.data.chatSessions as ChatSession[]
    const session = sessions.find(s => s.id === sessionId)
    
    if (session) {
      this.setData({
        messages: [...session.messages],
        currentSessionId: sessionId,
        historyVisible: false,
        scrollIntoView: session.messages[session.messages.length - 1]?.id || 'msg-welcome'
      })
    }
  },

  deleteSession(event: WechatMiniprogram.CustomEvent): void {
    event.stopPropagation?.()
    
    const sessionId = event.currentTarget.dataset.sessionId as string
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条会话记录吗？',
      success: (res) => {
        if (res.confirm) {
          let sessions = this.data.chatSessions as ChatSession[]
          sessions = sessions.filter(s => s.id !== sessionId)
          
          this.saveChatSessions(sessions)
          this.setData({
            chatSessions: sessions
          })
          
          if (this.data.currentSessionId === sessionId) {
            this.createNewSession()
          }
        }
      }
    })
  },

  saveCurrentSession(): void {
    const messages = this.data.messages as ChatMessage[]
    if (messages.length <= 1 && messages[0]?.content === GREETING) {
      return
    }

    let sessions = this.data.chatSessions as ChatSession[]
    let sessionId = this.data.currentSessionId as string
    
    if (!sessionId) {
      sessionId = `session-${Date.now()}`
      this.setData({ currentSessionId: sessionId })
    }

    const title = this.buildSessionTitle(messages)
    const preview = this.buildSessionPreview(messages)
    const updatedAt = this.formatTime(new Date())

    const existingIndex = sessions.findIndex(s => s.id === sessionId)
    
    const newSession: ChatSession = {
      id: sessionId,
      title,
      preview,
      updatedAt,
      messages: [...messages]
    }

    if (existingIndex >= 0) {
      sessions[existingIndex] = newSession
    } else {
      sessions.unshift(newSession)
    }

    if (sessions.length > MAX_SESSIONS) {
      sessions = sessions.slice(0, MAX_SESSIONS)
    }

    this.saveChatSessions(sessions)
    this.setData({ chatSessions: sessions })
  },

  buildSessionTitle(messages: ChatMessage[]): string {
    const userMessage = messages.find(m => m.role === 'user')
    if (!userMessage) {
      return '新对话'
    }
    
    const content = userMessage.content
    const maxLength = 12
    if (content.length <= maxLength) {
      return content
    }
    return content.substring(0, maxLength) + '...'
  },

  buildSessionPreview(messages: ChatMessage[]): string {
    if (messages.length === 0) {
      return ''
    }
    
    const lastMessage = messages[messages.length - 1]
    const content = lastMessage.content
    const maxLength = 20
    if (content.length <= maxLength) {
      return content
    }
    return content.substring(0, maxLength) + '...'
  },

  formatTime(date: Date): string {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    
    return `${year}-${month}-${day} ${hours}:${minutes}`
  },

  onInputChange(event: WechatMiniprogram.CustomEvent) {
    const inputValue = event.detail.value as string
    const trimmedValue = inputValue.trim()

    this.setData({
      inputValue,
      canSend: trimmedValue.length > 0
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

  onShuffleQuestions() {
    this.setData({
      commonQuestions: getRandomQuestions()
    })
  },

  async submitQuestion(question: string) {
    const timestamp = Date.now()
    const userMessage = createUserMessage(`msg-user-${timestamp}`, question)
    const placeholderMessage = createAssistantMessage(
      `msg-assistant-placeholder-${timestamp}`,
      '正在思考中...',
      '智能助手'
    )

    this.setData({
      messages: [...this.data.messages, userMessage, placeholderMessage],
      inputValue: '',
      canSend: false,
      isSending: true
    })

    setTimeout(() => {
      this.setData({ scrollIntoView: 'bottom-anchor' })
    }, 100)

    try {
      const response = await requestAssistantReply({
        assistantId: 'xiaohui' as AssistantId,
        question,
        chatId: this.data.chatId || undefined
      })

      console.log('========== 接口返回结果 ==========')
      console.log('response:', JSON.stringify(response, null, 2))
      console.log('response.content:', response.content)
      console.log('==================================')

      // 校验回复内容是否有效
      const replyContent = (response.content || '').trim()
      let finalContent = replyContent

      if (!replyContent) {
        finalContent = '抱歉，智能助手暂时没有获取到回复，请稍后再试。'
      }

      console.log('========== 更新消息前 ==========')
      console.log('placeholderMessage.id:', placeholderMessage.id)
      console.log('当前 messages 数组长度:', this.data.messages.length)
      const loadingMsg = this.data.messages.find(m => m.id === placeholderMessage.id)
      console.log('找到的 loading 消息:', loadingMsg ? JSON.stringify(loadingMsg, null, 2) : '未找到')
      console.log('==================================')

      const updatedMessages = this.data.messages.map(msg => 
        msg.id === placeholderMessage.id 
          ? createAssistantMessage(
              `msg-assistant-${Date.now()}`,
              finalContent,
              '智能助手'
            )
          : msg
      )

      console.log('========== 更新消息后 ==========')
      console.log('updatedMessages 数组长度:', updatedMessages.length)
      const assistantMsg = updatedMessages.find(m => m.role === 'assistant' && m.content !== '正在思考中...')
      console.log('最终 assistant 消息:', assistantMsg ? JSON.stringify(assistantMsg, null, 2) : '未找到')
      console.log('==================================')

      this.setData({
        messages: updatedMessages,
        chatId: response.chatId || this.data.chatId
      })

      setTimeout(() => {
        this.setData({ scrollIntoView: 'bottom-anchor' })
      }, 100)
    } catch (error) {
      console.error('AI回复请求失败:', error)
      
      const errorMessage = error instanceof Error 
        ? error.message 
        : '抱歉，智能助手服务暂时异常，请稍后再试。'

      const updatedMessages = this.data.messages.map(msg => 
        msg.id === placeholderMessage.id 
          ? createAssistantMessage(
              `msg-assistant-error-${Date.now()}`,
              errorMessage.includes('timeout') 
                ? '抱歉，智能助手响应较慢，请稍后重试。' 
                : '抱歉，智能助手服务暂时异常，请稍后再试。',
              '智能助手'
            )
          : msg
      )

      this.setData({
        messages: updatedMessages
      })

      setTimeout(() => {
        this.setData({ scrollIntoView: 'bottom-anchor' })
      }, 100)
    } finally {
      this.setData({
        isSending: false
      })
      this.saveCurrentSession()
    }
  },

  // 附件面板相关方法
  toggleAttachmentPanel(): void {
    this.setData({
      showAttachmentPanel: !this.data.showAttachmentPanel
    })
  },

  closeAttachmentPanel(): void {
    this.setData({
      showAttachmentPanel: false
    })
  },

  // 麦克风点击
  onVoiceClick(): void {
    wx.showToast({
      title: '语音功能开发中',
      icon: 'none'
    })
  },

  // 拍照
  onTakePhoto(): void {
    this.closeAttachmentPanel()
    
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera'],
      success: (res) => {
        this.handleMediaSelect(res.tempFiles)
      },
      fail: (error) => {
        console.error('拍照失败:', error)
        wx.showToast({
          title: '拍照失败',
          icon: 'none'
        })
      }
    })
  },

  // 从相册选择图片
  onChooseImage(): void {
    this.closeAttachmentPanel()
    
    wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        this.handleMediaSelect(res.tempFiles)
      },
      fail: (error) => {
        console.error('选择图片失败:', error)
        wx.showToast({
          title: '选择图片失败',
          icon: 'none'
        })
      }
    })
  },

  // 选择文件
  onChooseFile(): void {
    this.closeAttachmentPanel()
    
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      success: (res) => {
        this.handleFileSelect(res.tempFiles, 'file')
      },
      fail: (error) => {
        console.error('选择文件失败:', error)
        wx.showToast({
          title: '选择文件失败',
          icon: 'none'
        })
      }
    })
  },

  // 选择报告（复用文件选择）
  onChooseReport(): void {
    this.closeAttachmentPanel()
    
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      success: (res) => {
        this.handleFileSelect(res.tempFiles, 'report')
      },
      fail: (error) => {
        console.error('选择报告失败:', error)
        wx.showToast({
          title: '选择报告失败',
          icon: 'none'
        })
      }
    })
  },

  // 处理媒体选择结果
  handleMediaSelect(files: WechatMiniprogram.ChooseMediaFile[]): void {
    if (!files || files.length === 0) {
      return
    }

    files.forEach((file) => {
      const timestamp = Date.now()
      const imageMessage = createUserMessage(
        `msg-user-${timestamp}`,
        '[图片]',
        'image',
        file.tempFilePath,
        file.name,
        file.size
      )

      this.setData({
        messages: [...this.data.messages, imageMessage]
      })

      setTimeout(() => {
        this.setData({ scrollIntoView: 'bottom-anchor' })
      }, 100)

      // TODO: 后续实现图片上传和AI解析逻辑
      this.saveCurrentSession()
    })
  },

  // 处理文件选择结果
  handleFileSelect(files: WechatMiniprogram.ChooseMessageFile[], type: 'file' | 'report'): void {
    if (!files || files.length === 0) {
      return
    }

    files.forEach((file) => {
      const timestamp = Date.now()
      const content = type === 'report' ? '[报告]' : '[文件]'
      const fileMessage = createUserMessage(
        `msg-user-${timestamp}`,
        `${content} ${file.name}`,
        'file',
        file.path,
        file.name,
        file.size,
        this.formatFileSize(file.size)
      )

      this.setData({
        messages: [...this.data.messages, fileMessage]
      })

      setTimeout(() => {
        this.setData({ scrollIntoView: 'bottom-anchor' })
      }, 100)

      // TODO: 后续实现文件上传和 AI 解析逻辑
      this.saveCurrentSession()
    })
  },

  // 格式化文件大小
  formatFileSize(size: number): string {
    if (size < 1024) {
      return `${size}B`
    }
    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(1)}KB`
    }
    return `${(size / (1024 * 1024)).toFixed(1)}MB`
  }
})