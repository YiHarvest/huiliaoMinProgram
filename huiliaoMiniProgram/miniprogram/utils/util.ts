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

const CHAT_PROXY_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'
const CHAT_REQUEST_TIMEOUT = 30000

export function requestAssistantReply(payload: ChatRequestPayload): Promise<ChatReply> {
  console.log('========== AI 助手请求开始 ==========')
  console.log('请求地址:', `${CHAT_PROXY_BASE_URL}/api/chat`)
  console.log('请求方法: POST')
  console.log('请求 payload:', JSON.stringify(payload, null, 2))
  console.log('请求 payload 字段:', Object.keys(payload))
  console.log('=====================================')

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${CHAT_PROXY_BASE_URL}/api/chat`,
      method: 'POST',
      timeout: CHAT_REQUEST_TIMEOUT,
      data: payload,
      header: {
        'content-type': 'application/json'
      },
      success: res => {
        console.log('========== AI 助手响应 ==========')
        console.log('statusCode:', res.statusCode)
        console.log('headers:', res.header)
        console.log('data 原始返回:', JSON.stringify(res.data, null, 2))
        console.log('data 类型:', typeof res.data)
        console.log('==================================')

        if (res.statusCode === 502) {
          console.error('后端服务异常: 502 Bad Gateway')
          reject(new Error('后端服务异常，请稍后再试'))
          return
        }

        if (res.statusCode < 200 || res.statusCode >= 300) {
          const errorData = (res.data || {}) as ChatErrorReply
          console.error('请求失败，statusCode:', res.statusCode, 'errorData:', errorData)
          reject(new Error(errorData.error || '智能助手服务调用失败'))
          return
        }

        const data = (res.data || {}) as Partial<ChatReply>
        console.log('解析后 data.content 字段:', data.content)
        console.log('解析后 data 全部字段:', Object.keys(data))

        if (!data.content) {
          console.error('接口返回 content 字段为空或不存在')
          console.error('可能的替代字段:', Object.keys(data))
          reject(new Error('智能助手未返回有效内容'))
          return
        }

        const result: ChatReply = {
          assistantId: (data.assistantId as AssistantId) || payload.assistantId,
          content: data.content,
          chatId: data.chatId
        }
        console.log('解析后最终结果:', JSON.stringify(result, null, 2))
        console.log('==================================')

        resolve(result)
      },
      fail: error => {
        console.error('========== AI 助手请求失败 ==========')
        console.error('error:', error)
        console.error('errMsg:', error.errMsg)
        console.error('errorType:', error.type)
        console.error('statusCode:', error.statusCode)
        console.error('=====================================')

        const errMsg = error.errMsg || '智能助手服务请求失败'

        if (errMsg.includes('timeout')) {
          reject(new Error(`智能助手响应较慢，请稍后重试（请求超时 ${CHAT_REQUEST_TIMEOUT / 1000} 秒）`))
          return
        }

        reject(new Error(errMsg))
      }
    })
  })
}
