import { formatDisplayDate } from '../../utils/date'

type AnalysisBlock = {
  type: 'title' | 'paragraph'
  text: string
}

function cleanAnalysisText(value: unknown): string {
  return String(value || '')
    .replace(/\*\*/g, '')
    .replace(/```/g, '')
    .replace(/^\s*#+\s*/gm, '')
    .trim()
}

function parseAnalysisBlocks(value: unknown): AnalysisBlock[] {
  const cleaned = cleanAnalysisText(value)
  if (!cleaned) {
    return []
  }

  return cleaned
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => ({
      type: /^[一二三四五]、/.test(line) ? 'title' : 'paragraph',
      text: line
    }))
}

Page({
  data: {
    loading: true,
    error: false,
    errorMsg: '',
    recordId: '',
    title: '',
    questionnaireName: '',
    doctorName: '',
    completedAt: '',
    updatedAt: '',
    analysisText: '',
    analysisBlocks: [] as AnalysisBlock[]
  },

  onLoad(options: Record<string, string | undefined>) {
    const { recordId, title } = options || {}

    if (recordId) {
      this.setData({
        recordId,
        title: decodeURIComponent(title || '')
      })
      this.loadData()
    } else {
      this.setData({
        loading: false,
        error: true,
        errorMsg: '缺少记录ID参数'
      })
    }
  },

  async loadData() {
    this.setData({ loading: true, error: false })

    try {
      const res = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
        wx.request({
          url: 'https://miniprogram.huiliaoyiyuan.com/api/questionnaires/records/detail',
          method: 'GET',
          data: { recordId: this.data.recordId },
          header: {
            'Content-Type': 'application/json'
          },
          success: resolve,
          fail: reject
        })
      })

      if (res.statusCode === 200 && res.data && (res.data as any).success !== false) {
        const data = ((res.data as any).data || res.data) as any
        const cleanedText = cleanAnalysisText(data.analysisText || data.analysis || data.result || '')

        this.setData({
          loading: false,
          questionnaireName: data.questionnaireName || '',
          doctorName: data.doctorName || '',
          analysisText: cleanedText,
          analysisBlocks: parseAnalysisBlocks(cleanedText),
          completedAt: data.completedAt || (data.createdAt ? formatDisplayDate(data.createdAt) : ''),
          updatedAt: data.updatedAt ? formatDisplayDate(data.updatedAt) : ''
        })
      } else {
        throw new Error((res.data as any)?.error || '加载失败')
      }
    } catch (err: any) {
      console.error('[scale-result] 加载数据失败:', err)

      this.setData({
        loading: false,
        error: true,
        errorMsg: err.message || '加载失败，请稍后重试'
      })
    }
  }
})
