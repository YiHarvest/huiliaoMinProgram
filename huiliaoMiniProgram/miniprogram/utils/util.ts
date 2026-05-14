export const formatTime = (date: Date) => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return (
    [year, month, day].map(formatNumber).join('/') +
    ' ' +
    [hour, minute, second].map(formatNumber).join(':')
  )
}

const formatNumber = (n: number) => {
  const s = n.toString()
  return s[1] ? s : '0' + s
}

export type AssistantId = 'xiaohui' | 'chen'

type ChatRequestPayload = {
  assistantId: AssistantId
  question: string
  chatId?: string
  sessionId?: string
  userId?: string | number
  openid?: string
}

export type ChatReply = {
  assistantId: AssistantId
  content: string
  chatId?: string
  sessionId?: string
  replyId?: string
}

type ChatErrorReply = {
  error?: string
}

const CHAT_PROXY_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'
const CHAT_REQUEST_TIMEOUT = 30000
const REQUEST_RETRY_LIMIT = 2
const REQUEST_RETRY_DELAY = 1000

export type ChatSessionSummary = {
  sessionUuid: string
  userId?: string | number | null
  openid?: string | null
  assistantId: AssistantId | string
  llmChatId?: string | null
  title: string
  preview?: string | null
  messageCount?: number
  lastMessageAt?: string
  deletedAt?: string | null
  createdAt?: string
  updatedAt?: string
}

export type ChatHistoryMessage = {
  messageUuid: string
  sessionUuid: string
  role: 'user' | 'assistant' | 'system'
  messageType: 'text' | 'image' | 'file' | string
  content?: string | null
  mediaUrl?: string | null
  fileName?: string | null
  fileSize?: number | null
  extraJson?: string | null
  sortNo?: number
  llmReplyId?: string | null
  deletedAt?: string | null
  createdAt?: string
}

type ChatIdentity = {
  userId?: string | number
  openid?: string
}

type ChatListResponse = {
  sessions?: ChatSessionSummary[]
}

type ChatMessagesResponse = {
  sessionId?: string
  messages?: ChatHistoryMessage[]
}

export function requestAssistantReply(payload: ChatRequestPayload): Promise<ChatReply> {
  return new Promise((resolve, reject) => {
    const requestUrl = `${CHAT_PROXY_BASE_URL}/api/chat`
    console.log('[util] requestAssistantReply:', requestUrl, 'payload:', payload)
    
    wx.request({
      url: requestUrl,
      method: 'POST',
      timeout: CHAT_REQUEST_TIMEOUT,
      data: payload,
      header: {
        'content-type': 'application/json'
      },
      success: res => {
        console.log('[util] requestAssistantReply success, statusCode:', res.statusCode)
        
        if (res.statusCode === 502 || res.statusCode === 503) {
          reject(new Error('后端服务暂时不可用（' + res.statusCode + '），请稍后重试'))
          return
        }

        if (res.statusCode < 200 || res.statusCode >= 300) {
          const errorData = (res.data || {}) as ChatErrorReply
          reject(new Error(errorData.error || '智能助手服务调用失败 (' + res.statusCode + ')'))
          return
        }

        const data = (res.data || {}) as Partial<ChatReply>
        if (!data.content) {
          reject(new Error('智能助手未返回有效内容'))
          return
        }

        resolve({
          assistantId: (data.assistantId as AssistantId) || payload.assistantId,
          content: data.content,
          chatId: data.chatId,
          sessionId: data.sessionId,
          replyId: data.replyId
        })
      },
      fail: error => {
        console.error('[util] requestAssistantReply fail:', error)
        const errMsg = error.errMsg || '智能助手服务请求失败'
        if (errMsg.includes('timeout')) {
          reject(new Error(`智能助手响应较慢，请稍后重试（超时 ${CHAT_REQUEST_TIMEOUT / 1000} 秒）`))
          return
        }

        if (errMsg.includes('url')) {
          reject(new Error('网络地址错误，请检查配置'))
          return
        }

        reject(new Error(errMsg))
      }
    })
  })
}

export function requestChatSessions(
  identity: ChatIdentity & { assistantId?: AssistantId | string } = {}
): Promise<ChatSessionSummary[]> {
  const queryParts: string[] = []

  if (identity.userId !== undefined && identity.userId !== null && `${identity.userId}`.trim() !== '') {
    queryParts.push(`userId=${encodeURIComponent(`${identity.userId}`)}`)
  }
  if (identity.openid) {
    queryParts.push(`openid=${encodeURIComponent(identity.openid)}`)
  }
  if (identity.assistantId) {
    queryParts.push(`assistantId=${encodeURIComponent(identity.assistantId)}`)
  }

  const query = queryParts.join('&')

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${CHAT_PROXY_BASE_URL}/api/chat/sessions${query ? `?${query}` : ''}`,
      method: 'GET',
      timeout: CHAT_REQUEST_TIMEOUT,
      header: {
        'content-type': 'application/json'
      },
      success: res => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const errorData = (res.data || {}) as ChatErrorReply
          reject(new Error(errorData.error || '获取历史会话失败'))
          return
        }

        const data = (res.data || {}) as ChatListResponse
        resolve(Array.isArray(data.sessions) ? data.sessions : [])
      },
      fail: error => {
        reject(new Error(error.errMsg || '网络请求失败'))
      }
    })
  })
}

export function requestChatMessages(sessionId: string): Promise<ChatHistoryMessage[]> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${CHAT_PROXY_BASE_URL}/api/chat/messages?sessionId=${encodeURIComponent(sessionId)}`,
      method: 'GET',
      timeout: CHAT_REQUEST_TIMEOUT,
      header: {
        'content-type': 'application/json'
      },
      success: res => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const errorData = (res.data || {}) as ChatErrorReply
          reject(new Error(errorData.error || '获取会话消息失败'))
          return
        }

        const data = (res.data || {}) as ChatMessagesResponse
        resolve(Array.isArray(data.messages) ? data.messages : [])
      },
      fail: error => {
        reject(new Error(error.errMsg || '网络请求失败'))
      }
    })
  })
}

export function deleteChatSession(sessionId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${CHAT_PROXY_BASE_URL}/api/chat/session/delete`,
      method: 'POST',
      timeout: CHAT_REQUEST_TIMEOUT,
      data: { sessionId },
      header: {
        'content-type': 'application/json'
      },
      success: res => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const errorData = (res.data || {}) as ChatErrorReply
          reject(new Error(errorData.error || '删除会话失败'))
          return
        }

        resolve()
      },
      fail: error => {
        reject(new Error(error.errMsg || '网络请求失败'))
      }
    })
  })
}
