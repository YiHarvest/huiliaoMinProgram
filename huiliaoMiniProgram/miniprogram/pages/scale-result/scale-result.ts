import { formatDisplayDate } from '../../utils/date'

type AnalysisBlock = {
  type: 'title' | 'paragraph'
  text: string
}

function cleanAnalysisText(value: unknown): string {
  let text = String(value || '')
    .replace(/\*\*/g, '')
    .replace(/```/g, '')
    .replace(/^\s*#+\s*/gm, '')
    .trim()

  text = removeDuplicateDisclaimer(text)

  return text
}

function removeDuplicateDisclaimer(text: string): string {
  const disclaimerSentence1 = '本量表结果仅为个人填写信息的客观呈现'
  const disclaimerSentence2 = '不构成任何诊断依据'
  const disclaimerSentence3 = '所有症状描述均为自我报告'
  const disclaimerSentence4 = '如后续需进一步沟通'

  const lines = text.split('\n')
  let foundFirstDisclaimerBlock = false
  const dedupedLines: string[] = []
  let inDisclaimerBlock = false
  let disclaimerBlockLines: string[] = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmedLine = line.trim()

    if (!trimmedLine) {
      if (inDisclaimerBlock && disclaimerBlockLines.length > 0) {
        if (!foundFirstDisclaimerBlock) {
          dedupedLines.push(...disclaimerBlockLines)
          foundFirstDisclaimerBlock = true
        }
        disclaimerBlockLines = []
        inDisclaimerBlock = false
      }
      dedupedLines.push(line)
      continue
    }

    const isDisclaimerLine =
      trimmedLine.includes(disclaimerSentence1) ||
      trimmedLine.includes(disclaimerSentence2) ||
      trimmedLine.includes(disclaimerSentence3) ||
      trimmedLine.includes(disclaimerSentence4)

    if (isDisclaimerLine) {
      if (!inDisclaimerBlock) {
        inDisclaimerBlock = true
        disclaimerBlockLines = []
      }
      disclaimerBlockLines.push(line)
    } else {
      if (inDisclaimerBlock && disclaimerBlockLines.length > 0) {
        if (!foundFirstDisclaimerBlock) {
          dedupedLines.push(...disclaimerBlockLines)
          foundFirstDisclaimerBlock = true
        }
        disclaimerBlockLines = []
        inDisclaimerBlock = false
      }
      dedupedLines.push(line)
    }
  }

  if (inDisclaimerBlock && disclaimerBlockLines.length > 0) {
    if (!foundFirstDisclaimerBlock) {
      dedupedLines.push(...disclaimerBlockLines)
    }
  }

  return dedupedLines.join('\n')
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
      type: /^[\u4e00\u4e8c\u4e09\u56db\u4e94]\u3001/.test(line) ? 'title' : 'paragraph',
      text: line
    }))
}

const QUESTIONNAIRE_AI_GENERATING_TEXT = 'AI分析生成中，请稍后查看'
const QUESTIONNAIRE_AI_GENERATING_HINT = 'AI分析生成中，请稍后刷新查看'

function isGeneratingAnalysisText(value: unknown): boolean {
  const text = String(value || '').trim()
  return !text || text === QUESTIONNAIRE_AI_GENERATING_TEXT
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
    analysisStatus: '',
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
        const rawAnalysisText = data.analysisText || data.analysis || data.result || ''
        const analysisStatus = String(data.analysisStatus || '').trim() || (isGeneratingAnalysisText(rawAnalysisText) ? 'generating' : '')
        const cleanedText = cleanAnalysisText(rawAnalysisText)
        const isGenerating = analysisStatus === 'generating' || isGeneratingAnalysisText(rawAnalysisText)
        const displayText = isGenerating ? QUESTIONNAIRE_AI_GENERATING_HINT : cleanedText

        this.setData({
          loading: false,
          questionnaireName: data.questionnaireName || '',
          doctorName: data.doctorName || '',
          analysisStatus,
          analysisText: displayText,
          analysisBlocks: isGenerating ? [] : parseAnalysisBlocks(cleanedText),
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
