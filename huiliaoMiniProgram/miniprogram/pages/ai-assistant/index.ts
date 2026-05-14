import {
  AssistantId,
  ChatHistoryMessage,
  ChatSessionSummary,
  deleteChatSession,
  requestAssistantReply,
  requestChatMessages,
  requestChatSessions
} from '../../utils/util'

let voiceManager: any = null
let voicePluginAvailable = false
let voiceTimer: number | null = null
let voiceStoppingTimer: number | null = null

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
  isLoading?: boolean
}

type CommonQuestion = {
  id: string
  text: string
}

type UserIdentity = {
  userId: string | number | null
  openid: string
}

type PendingAttachment =
  | {
      type: 'image'
      mediaUrl: string
      fileName?: string
      fileSize?: number
    }
  | {
      type: 'file'
      mediaUrl: string
      fileName?: string
      fileSize?: number
      fileSizeText?: string
    }

type QueuedQuestion = {
  requestId: string
  question: string
  sessionId: string
  chatId?: string
  attachments: PendingAttachment[]
  userMessageId: string
  assistantMessageId: string
}

const questionPool = [
  '备孕前需要提前准备哪些事项？',
  '月经不规律要先做什么检查？',
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

const GREETING =
  '您好，我是智能助手，可以为您提供妇科、男科、备孕、报告解读等相关健康咨询建议。请描述您的问题，我会尽量帮您分析。'

function createAssistantMessage(id: string, content: string, label: string): ChatMessage {
  return {
    id,
    role: 'assistant',
    content,
    label,
    type: 'text',
    isLoading: content === '正在思考中...' || content === '正在排队中...'
  }
}

function createUserMessage(
  id: string,
  content: string,
  type?: 'text' | 'image' | 'file',
  mediaUrl?: string,
  fileName?: string,
  fileSize?: number,
  fileSizeText?: string
): ChatMessage {
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
    const j = Math.floor(Math.random() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

function getRandomQuestions(): CommonQuestion[] {
  return shuffleArray(questionPool)
    .slice(0, 4)
    .map((text, index) => ({
      id: `question-${index + 1}`,
      text
    }))
}

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size}B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)}KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)}MB`
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function mapServerMessage(message: ChatHistoryMessage): ChatMessage {
  const role = message.role === 'assistant' ? 'assistant' : 'user'
  const type = (message.messageType as 'text' | 'image' | 'file') || 'text'
  const fallbackContent =
    type === 'image'
      ? '[图片]'
      : type === 'file'
        ? message.fileName
          ? `[文件] ${message.fileName}`
          : '[文件]'
        : ''

  return {
    id: message.messageUuid,
    role,
    content: (message.content || fallbackContent || '').trim(),
    label: role === 'assistant' ? '智能助手' : '我',
    type,
    mediaUrl: message.mediaUrl || undefined,
    fileName: message.fileName || undefined,
    fileSize: message.fileSize || undefined,
    fileSizeText: typeof message.fileSize === 'number' ? formatFileSize(message.fileSize) : undefined
  }
}

Page({
  data: {
    commonQuestions: getRandomQuestions() as CommonQuestion[],
    messages: [createAssistantMessage('msg-welcome', GREETING, '智能助手')] as ChatMessage[],
    inputValue: '',
    canSend: false,
    isSending: false,
    chatId: '',
    scrollIntoView: 'msg-welcome',
    historyVisible: false,
    currentSessionId: '',
    chatSessions: [] as ChatSessionSummary[],
    pendingCount: 0,
    statusBarHeight: 0,
    navBarHeight: 0,
    showAttachmentPanel: false,
    isRecording: false,
    isRecognizing: false,
    voiceStopping: false
  },

  pendingQueue: [] as QueuedQuestion[],
  isProcessingQueue: false,

  onLoad(): void {
    this.initNavBarHeight()
    this.initVoicePlugin()
    void this.loadChatSessions()
  },

  initVoicePlugin(): void {
    console.log('[voice] 开始初始化语音插件...')

    try {
      const plugin = requirePlugin('WechatSI')
      console.log('[voice] 插件加载成功:', plugin)

      if (plugin && typeof plugin.getRecordRecognitionManager === 'function') {
        voiceManager = plugin.getRecordRecognitionManager()
        voicePluginAvailable = true
        console.log('[voice] 语音管理器初始化成功')
        this.initVoiceRecognitionCallbacks()
      } else {
        console.error('[voice] 插件API不可用')
        voicePluginAvailable = false
      }
    } catch (e) {
      console.error('[voice] 插件加载失败:', e)
      voicePluginAvailable = false
    }
  },

  initVoiceRecognitionCallbacks(): void {
    if (!voiceManager) {
      console.warn('[voice] voiceManager 不存在，跳过回调注册')
      return
    }

    console.log('[voice] ========== 开始诊断 voiceManager ==========')
    console.log('[voice] manager raw:', voiceManager)
    console.log('[voice] manager type:', typeof voiceManager)
    console.log('[voice] manager keys:', Object.keys(voiceManager || {}))
    console.log('[voice] typeof onStart:', typeof voiceManager.onStart)
    console.log('[voice] typeof onRecognize:', typeof voiceManager.onRecognize)
    console.log('[voice] typeof onStop:', typeof voiceManager.onStop)
    console.log('[voice] typeof onError:', typeof voiceManager.onError)
    console.log('[voice] typeof start:', typeof voiceManager.start)
    console.log('[voice] typeof stop:', typeof voiceManager.stop)
    console.log('[voice] ========== 诊断结束 ==========')

    const self = this

    try {
      voiceManager.onStart = function() {
        console.log('[voice] ✓ onStart 回调触发（属性赋值方式）')
        self.setData({ isRecording: true, isRecognizing: true })
      }
      console.log('[voice] onStart 已设置（属性赋值）')
    } catch (e) {
      console.error('[voice] 设置 onStart 失败（属性赋值）:', e)

      try {
        voiceManager.onStart(function() {
          console.log('[voice] ✓ onStart 回调触发（函数调用方式）')
          self.setData({ isRecording: true, isRecognizing: true })
        })
        console.log('[voice] onStart 已设置（函数调用）')
      } catch (e2) {
        console.error('[voice] 设置 onStart 也失败（函数调用）:', e2)
      }
    }

    if (typeof voiceManager.onRecognize !== 'undefined') {
      try {
        voiceManager.onRecognize = function(res: any) {
          console.log('[voice] onRecognize 回调触发（属性赋值） raw:', res)
        }
        console.log('[voice] onRecognize 已设置（属性赋值）')
      } catch (e) {
        console.error('[voice] 设置 onRecognize 失败（属性赋值）:', e)

        try {
          if (typeof voiceManager.onRecognize === 'function') {
            voiceManager.onRecognize(function(res: any) {
              console.log('[voice] onRecognize 回调触发（函数调用） raw:', res)
            })
            console.log('[voice] onRecognize 已设置（函数调用）')
          }
        } catch (e2) {
          console.error('[voice] 设置 onRecognize 也失败:', e2)
        }
      }
    }

    try {
      voiceManager.onStop = function(res: any) {
        console.log('[voice] ✓ onStop 回调触发（属性赋值方式）')
        console.log('[voice] onStop raw response:', res)
        console.log('[voice] onStop keys:', Object.keys(res || {}))

        self.clearVoiceTimer()
        self.clearVoiceStoppingTimer()
        self.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })

        const text = String(res?.result || res?.resultText || res?.text || '').trim()
        console.log('[voice] 识别到的文本:', text)

        if (text.length > 0) {
          console.log('[voice] 调用 submitQuestion 发送:', text)
          void self.submitQuestion(text)
        } else {
          console.warn('[voice] 识别结果为空')
          wx.showToast({
            title: '未识别到语音内容，请重新说一遍或改用文字输入',
            icon: 'none',
            duration: 2500
          })
        }
      }
      console.log('[voice] onStop 已设置（属性赋值）')
    } catch (e) {
      console.error('[voice] 设置 onStop 失败（属性赋值）:', e)

      try {
        voiceManager.onStop(function(res: any) {
          console.log('[voice] ✓ onStop 回调触发（函数调用方式）')
          console.log('[voice] onStop raw response:', res)
          console.log('[voice] onStop keys:', Object.keys(res || {}))

          self.clearVoiceTimer()
          self.clearVoiceStoppingTimer()
          self.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })

          const text = String(res?.result || res?.resultText || res?.text || '').trim()
          console.log('[voice] 识别到的文本:', text)

          if (text.length > 0) {
            console.log('[voice] 调用 submitQuestion 发送:', text)
            void self.submitQuestion(text)
          } else {
            console.warn('[voice] 识别结果为空')
            wx.showToast({
              title: '未识别到语音内容，请重新说一遍或改用文字输入',
              icon: 'none',
              duration: 2500
            })
          }
        })
        console.log('[voice] onStop 已设置（函数调用）')
      } catch (e2) {
        console.error('[voice] 设置 onStop 也失败（函数调用）:', e2)
      }
    }

    try {
      voiceManager.onError = function(err: any) {
        console.error('[voice] ✗ onError 回调触发（属性赋值） raw:', err)

        self.clearVoiceTimer()
        self.clearVoiceStoppingTimer()
        self.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })
        wx.showToast({
          title: '语音识别失败，请重试或使用文字输入',
          icon: 'none',
          duration: 2000
        })
      }
      console.log('[voice] onError 已设置（属性赋值）')
    } catch (e) {
      console.error('[voice] 设置 onError 失败（属性赋值）:', e)

      try {
        voiceManager.onError(function(err: any) {
          console.error('[voice] ✗ onError 回调触发（函数调用） raw:', err)

          self.clearVoiceTimer()
          self.clearVoiceStoppingTimer()
          self.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })
          wx.showToast({
            title: '语音识别失败，请重试或使用文字输入',
            icon: 'none',
            duration: 2000
          })
        })
        console.log('[voice] onError 已设置（函数调用）')
      } catch (e2) {
        console.error('[voice] 设置 onError 也失败（函数调用）:', e2)
      }
    }

    console.log('[voice] ✓✓✓ 所有回调注册完成 ✓✓✓')
  },

  onUnload(): void {
    this.clearVoiceTimer()
    this.clearVoiceStoppingTimer()

    if ((this.data.isRecording || this.data.isRecognizing) && voiceManager) {
      try {
        voiceManager.stop()
      } catch (e) {
        console.log('[voice] 卸载时停止录音')
      }
    }
    this.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })
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

  async ensureLoginReady(): Promise<void> {
    const app = getApp<any>()
    if (app && typeof app.ensureLogin === 'function') {
      await app.ensureLogin()
    }
  },

  syncQueueState(): void {
    this.setData({
      isSending: this.isProcessingQueue,
      pendingCount: this.pendingQueue.length + (this.isProcessingQueue ? 1 : 0)
    })
  },

  getCurrentIdentity(): UserIdentity {
    const app = getApp<any>()
    const globalProfile = app?.globalData?.userProfile || {}
    const globalUserId = app?.globalData?.userId || 0

    const storedProfile = (() => {
      const raw = wx.getStorageSync('USER_PROFILE')
      if (!raw) {
        return {}
      }
      if (typeof raw === 'string') {
        try {
          return JSON.parse(raw)
        } catch {
          return {}
        }
      }
      return raw
    })()

    return {
      userId: globalUserId || storedProfile.userId || storedProfile.id || globalProfile.userId || null,
      openid: globalProfile.openid || storedProfile.openid || wx.getStorageSync('openid') || ''
    }
  },

  getCurrentSessionId(): string {
    return this.data.currentSessionId || `session-${Date.now()}`
  },

  hasPendingWork(): boolean {
    return this.isProcessingQueue || this.pendingQueue.length > 0
  },

  async loadChatSessions(): Promise<void> {
    await this.ensureLoginReady()
    const identity = this.getCurrentIdentity()

    try {
      const sessions = await requestChatSessions({
        userId: identity.userId || undefined,
        openid: identity.openid || undefined,
        assistantId: 'xiaohui'
      })

      this.setData({
        chatSessions: sessions
      })

      if (!this.data.currentSessionId && sessions.length > 0) {
        this.setData({
          currentSessionId: sessions[0].sessionUuid,
          chatId: sessions[0].llmChatId || ''
        })
      }
    } catch (error) {
      console.error('加载历史会话失败:', error)
      this.setData({
        chatSessions: []
      })
    }
  },

  openHistoryDrawer(): void {
    void this.loadChatSessions()
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
    if (this.hasPendingWork()) {
      wx.showModal({
        title: '还有未完成消息',
        content: '当前还有问题在排队或正在回复中，切换新对话可能会影响上下文。请先等当前队列完成。',
        showCancel: false
      })
      return
    }

    this.setData({
      messages: [createAssistantMessage('msg-welcome', GREETING, '智能助手')],
      currentSessionId: '',
      chatId: '',
      historyVisible: false,
      showAttachmentPanel: false,
      scrollIntoView: 'msg-welcome'
    })
  },

  async openSession(session: ChatSessionSummary): Promise<void> {
    try {
      const messages = await requestChatMessages(session.sessionUuid)
      const mappedMessages =
        messages.length > 0
          ? messages.map(mapServerMessage)
          : [createAssistantMessage('msg-welcome', GREETING, '智能助手')]

      this.setData({
        messages: mappedMessages,
        currentSessionId: session.sessionUuid,
        chatId: session.llmChatId || '',
        historyVisible: false,
        showAttachmentPanel: false,
        scrollIntoView: mappedMessages[mappedMessages.length - 1]?.id || 'msg-welcome'
      })
    } catch (error) {
      console.error('切换历史会话失败:', error)
      wx.showToast({
        title: '加载历史失败',
        icon: 'none'
      })
    }
  },

  async switchSession(event: WechatMiniprogram.CustomEvent): Promise<void> {
    const sessionId = event.currentTarget.dataset.sessionId as string
    const session = this.data.chatSessions.find(item => item.sessionUuid === sessionId)

    if (!session) {
      return
    }

    if (this.hasPendingWork()) {
      wx.showModal({
        title: '还有未完成消息',
        content: '当前队列还没有发完，建议先等当前回复完成后再切换历史会话，避免消息上下文错乱。',
        showCancel: false
      })
      return
    }

    await this.openSession(session)
  },

  async deleteSession(event: WechatMiniprogram.CustomEvent): Promise<void> {
    event.stopPropagation?.()

    const sessionId = event.currentTarget.dataset.sessionId as string
    if (!sessionId) {
      return
    }

    if (this.hasPendingWork()) {
      wx.showToast({
        title: '请先完成当前队列',
        icon: 'none'
      })
      return
    }

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条历史会话吗？',
      success: async res => {
        if (!res.confirm) {
          return
        }

        try {
          await deleteChatSession(sessionId)
          const nextSessions = this.data.chatSessions.filter(item => item.sessionUuid !== sessionId)
          this.setData({
            chatSessions: nextSessions
          })

          if (this.data.currentSessionId === sessionId) {
            this.createNewSession()
          }
        } catch (error) {
          console.error('删除会话失败:', error)
          wx.showToast({
            title: '删除失败',
            icon: 'none'
          })
        }
      }
    })
  },

  onInputChange(event: WechatMiniprogram.CustomEvent): void {
    const inputValue = event.detail.value as string
    this.setData({
      inputValue,
      canSend: inputValue.trim().length > 0
    })
  },

  onTapCommonQuestion(event: WechatMiniprogram.CustomEvent): void {
    const question = event.currentTarget.dataset.question as string
    if (!question) {
      return
    }

    void this.submitQuestion(question)
  },

  onSendMessage(): void {
    if (!this.data.canSend) {
      return
    }

    const question = this.data.inputValue.trim()
    if (!question) {
      return
    }

    void this.submitQuestion(question)
  },

  onShuffleQuestions(): void {
    this.setData({
      commonQuestions: getRandomQuestions()
    })
  },

  enqueueQuestion(question: string, attachments: PendingAttachment[] = []): void {
    const now = Date.now()
    const sessionId = this.getCurrentSessionId()
    const requestId = `queue-${now}-${Math.random().toString(36).slice(2, 8)}`
    const userMessageId = `msg-user-${now}`
    const assistantMessageId = `msg-assistant-${now}`
    const queued = this.pendingQueue.length > 0 || this.isProcessingQueue

    this.pendingQueue.push({
      requestId,
      question,
      sessionId,
      chatId: this.data.chatId || undefined,
      attachments,
      userMessageId,
      assistantMessageId
    })

    this.setData({
      messages: [
        ...this.data.messages,
        createUserMessage(userMessageId, question),
        createAssistantMessage(assistantMessageId, queued ? '正在排队中...' : '正在思考中...', '智能助手')
      ],
      inputValue: '',
      canSend: false,
      currentSessionId: sessionId,
      showAttachmentPanel: false,
      scrollIntoView: 'bottom-anchor'
    })

    this.syncQueueState()
    void this.processQueue()
  },

  async submitQuestion(question: string): Promise<void> {
    this.enqueueQuestion(question)
  },

  async processQueue(): Promise<void> {
    if (this.isProcessingQueue) {
      return
    }

    const task = this.pendingQueue.shift()
    if (!task) {
      this.syncQueueState()
      return
    }

    this.isProcessingQueue = true
    this.syncQueueState()

    try {
      await this.ensureLoginReady()

      this.setData({
        messages: this.data.messages.map(msg =>
          msg.id === task.assistantMessageId
            ? { ...msg, content: '正在思考中...', isLoading: true }
            : msg
        ),
        scrollIntoView: 'bottom-anchor'
      })

      const identity = this.getCurrentIdentity()
      const response = await requestAssistantReply({
        assistantId: 'xiaohui' as AssistantId,
        question: task.question,
        chatId: this.data.chatId || task.chatId || undefined,
        sessionId: task.sessionId,
        userId: identity.userId || undefined,
        openid: identity.openid || undefined
      })

      const replyContent = (response.content || '').trim() || '抱歉，暂时没有获取到回复，请稍后再试。'
      const finalSessionId = response.sessionId || task.sessionId
      const finalChatId = response.chatId || this.data.chatId || task.chatId || ''

      this.setData({
        chatId: finalChatId,
        currentSessionId: finalSessionId
      })

      await this.typewriterReply(task.assistantMessageId, replyContent)
      void this.loadChatSessions()
    } catch (error) {
      console.error('队列任务处理失败:', error)

      const fallback =
        error instanceof Error && error.message.includes('timeout')
          ? '抱歉，智能助手响应较慢，请稍后重试。'
          : '抱歉，智能助手服务暂时异常，请稍后再试。'

      await this.typewriterReply(task.assistantMessageId, fallback)
    } finally {
      this.isProcessingQueue = false
      this.syncQueueState()
      void this.processQueue()
    }
  },

  async typewriterReply(messageId: string, text: string): Promise<void> {
    const target = (text || '').trim() || ' '
    console.log('[typewriter] start', messageId, target.length)
    let rendered = ''

    for (let i = 0; i < target.length; i++) {
      rendered += target[i]
      this.setData({
        messages: this.data.messages.map(msg =>
          msg.id === messageId
            ? { ...msg, content: rendered, isLoading: true }
            : msg
        ),
        scrollIntoView: 'bottom-anchor'
      })

      const currentChar = target[i]
      const delay = '，。！？；：,!?;:'.includes(currentChar) ? 120 : 40
      await sleep(delay)
    }

    console.log('[typewriter] complete', messageId)

    this.setData({
      messages: this.data.messages.map(msg =>
        msg.id === messageId
          ? { ...msg, content: target, isLoading: false }
          : msg
      ),
      scrollIntoView: 'bottom-anchor'
    })
  },

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

  onVoiceClick(): void {
    console.log('[voice] onVoiceClick 触发, voicePluginAvailable:', voicePluginAvailable, 'isRecognizing:', this.data.isRecognizing)

    if (!voicePluginAvailable) {
      console.warn('[voice] 插件不可用')
      wx.showToast({
        title: '语音功能暂不可用，请使用文字输入',
        icon: 'none',
        duration: 2000
      })
      return
    }

    if (this.data.isRecognizing) {
      this.stopVoiceRecognition()
    } else {
      this.startVoiceRecognition()
    }
  },

  startVoiceRecognition(): void {
    if (this.data.isRecognizing) return

    wx.getSetting({
      success: (res) => {
        if (res.authSetting['scope.record'] === false) {
          wx.showModal({
            title: '需要麦克风权限',
            content: '语音输入功能需要开启麦克风权限，是否前往设置？',
            confirmText: '去设置',
            cancelText: '取消',
            success: (modalRes) => {
              if (modalRes.confirm) {
                wx.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting['scope.record']) {
                      this.doStartRecognition()
                    }
                  }
                })
              }
            }
          })
        } else {
          this.doStartRecognition()
        }
      },
      fail: () => {
        this.doStartRecognition()
      }
    })
  },

  doStartRecognition(): void {
    console.log('[voice] doStartRecognition 调用, voiceManager:', !!voiceManager)

    if (!voiceManager) {
      console.error('[voice] voiceManager 不存在')
      wx.showToast({
        title: '语音功能暂不可用，请使用文字输入',
        icon: 'none',
        duration: 2000
      })
      return
    }

    try {
      console.log('[voice] 调用 voiceManager.start() with {lang:"zh_CN", duration:30000}')
      voiceManager.start({
        lang: 'zh_CN',
        duration: 30000
      })

      this.setData({ isRecording: true, isRecognizing: true, voiceStopping: false })
      console.log('[voice] voiceManager.start() 调用成功, 已设置录音状态 isRecognizing=true')

      this.clearVoiceTimer()
      voiceTimer = setTimeout(() => {
        console.log('[voice] 录音超时(15秒), 自动停止')
        if (this.data.isRecognizing) {
          this.stopVoiceRecognition()
        }
      }, 15000)
    } catch (e) {
      console.error('[voice] 启动失败', e)
      wx.showToast({
        title: '语音功能启动失败，请重试',
        icon: 'none',
        duration: 2000
      })
    }
  },

  stopVoiceRecognition(): void {
    console.log('[voice] stopVoiceRecognition 调用')

    this.clearVoiceTimer()

    if (!voiceManager) {
      console.warn('[voice] voiceManager 不存在，仅重置状态')
      this.setData({ isRecording: false, isRecognizing: false })
      return
    }

    try {
      voiceManager.stop()
      this.setData({ voiceStopping: true })
      console.log('[voice] voiceManager.stop() 调用成功, 等待 onStop 回调返回识别结果 (3秒超时兜底)')

      this.clearVoiceStoppingTimer()
      voiceStoppingTimer = setTimeout(() => {
        if (this.data.voiceStopping) {
          console.warn('[voice] ⚠️ stop 后 3 秒内未收到 onStop 回调，强制重置状态')
          this.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })
          wx.showToast({
            title: '语音识别未返回结果，请重试',
            icon: 'none',
            duration: 2000
          })
        }
      }, 3000)
    } catch (e) {
      console.error('[voice] 停止失败', e)
      this.setData({ isRecording: false, isRecognizing: false, voiceStopping: false })
    }
  },

  clearVoiceTimer(): void {
    if (voiceTimer !== null) {
      clearTimeout(voiceTimer)
      voiceTimer = null
      console.log('[voice] 定时器已清除')
    }
  },

  clearVoiceStoppingTimer(): void {
    if (voiceStoppingTimer !== null) {
      clearTimeout(voiceStoppingTimer)
      voiceStoppingTimer = null
      console.log('[voice] stop超时定时器已清除')
    }
  },

  onTakePhoto(): void {
    this.closeAttachmentPanel()

    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera'],
      success: res => {
        this.handleMediaSelect(res.tempFiles)
      },
      fail: error => {
        console.error('拍照失败:', error)
        wx.showToast({
          title: '拍照失败',
          icon: 'none'
        })
      }
    })
  },

  onChooseImage(): void {
    this.closeAttachmentPanel()

    wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
      sourceType: ['album'],
      success: res => {
        this.handleMediaSelect(res.tempFiles)
      },
      fail: error => {
        console.error('选择图片失败:', error)
        wx.showToast({
          title: '选择图片失败',
          icon: 'none'
        })
      }
    })
  },

  onChooseFile(): void {
    this.closeAttachmentPanel()

    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      success: res => {
        this.handleFileSelect(res.tempFiles, 'file')
      },
      fail: error => {
        console.error('选择文件失败:', error)
        wx.showToast({
          title: '选择文件失败',
          icon: 'none'
        })
      }
    })
  },

  onChooseReport(): void {
    this.closeAttachmentPanel()

    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      success: res => {
        this.handleFileSelect(res.tempFiles, 'report')
      },
      fail: error => {
        console.error('选择报告失败:', error)
        wx.showToast({
          title: '选择报告失败',
          icon: 'none'
        })
      }
    })
  },

  handleMediaSelect(files: WechatMiniprogram.ChooseMediaFile[]): void {
    if (!files || files.length === 0) {
      return
    }

    files.forEach(file => {
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
        messages: [...this.data.messages, imageMessage],
        scrollIntoView: 'bottom-anchor'
      })
    })
  },

  handleFileSelect(files: WechatMiniprogram.ChooseMessageFile[], type: 'file' | 'report'): void {
    if (!files || files.length === 0) {
      return
    }

    files.forEach(file => {
      const timestamp = Date.now()
      const prefix = type === 'report' ? '[报告]' : '[文件]'
      const fileMessage = createUserMessage(
        `msg-user-${timestamp}`,
        `${prefix} ${file.name}`,
        'file',
        file.path,
        file.name,
        file.size,
        formatFileSize(file.size)
      )

      this.setData({
        messages: [...this.data.messages, fileMessage],
        scrollIntoView: 'bottom-anchor'
      })
    })
  }
})
