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
}

export type ChatReply = {
  assistantId: AssistantId
  content: string
  chatId?: string
}

type ChatErrorReply = {
  error?: string
}

const CHAT_PROXY_BASE_URL = 'http://127.0.0.1:8010'

export function requestAssistantReply(payload: ChatRequestPayload): Promise<ChatReply> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${CHAT_PROXY_BASE_URL}/api/chat`,
      method: 'POST',
      timeout: 15000,
      data: payload,
      header: {
        'content-type': 'application/json'
      },
      success: res => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const errorData = (res.data || {}) as ChatErrorReply
          reject(new Error(errorData.error || '智能助手服务调用失败'))
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
          chatId: data.chatId
        })
      },
      fail: error => {
        reject(new Error(error.errMsg || '智能助手服务请求失败'))
      }
    })
  })
}
