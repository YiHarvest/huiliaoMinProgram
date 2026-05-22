const API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'

interface ReportBlock {
  text: string
  isHeading: boolean
  isBlank: boolean
}

function getDiseaseTypeName(value: unknown): string {
  const diseaseType = String(value || '').trim()
  const diseaseTypeMap: Record<string, string> = {
    premature_ejaculation: '早泄',
    male_sexual_dysfunction: '男性性功能障碍',
    prostatitis: '前列腺炎',
    infertility: '不孕不育',
    gynecology_general: '妇科症状',
    other_male_general: '男科一般问诊',
    other_gynecology_general: '妇科一般问诊',
    male_infertility: '男性不育',
    female_infertility: '女性不孕',
    male_sexual_function: '男性性功能问题',
    other_male: '男科其他问题',
    other_female: '妇科其他问题',
    menstrual_disorder: '月经紊乱',
    tcm_gyn: '中医妇科',
    tcm_constitution: '中医体质'
  }
  return diseaseTypeMap[diseaseType] || diseaseType || '未填写'
}

function getVisitTypeName(value: unknown): string {
  const visitType = String(value || '').trim()
  const visitTypeMap: Record<string, string> = {
    first: '初诊',
    followup: '复诊',
    referral: '转诊'
  }
  return visitTypeMap[visitType] || visitType || '未填写'
}

function cleanReportText(value: unknown): string {
  return String(value || '')
    .replace(/\*\*/g, '')
    .replace(/```/g, '')
    .replace(/\r\n?/g, '\n')
    .trim()
}

Page({
  data: {
    reportId: '',
    loading: false,
    error: false,
    errorMessage: '',
    report: {} as any,
    basis: {
      questionnaireNames: [] as string[],
      questionnaireRecordIds: [] as string[]
    },
    reportBlocks: [] as ReportBlock[]
  },

  onLoad(options: Record<string, string>) {
    const reportId = String(options.reportId || '').trim()
    if (!reportId) {
      this.setData({
        error: true,
        errorMessage: '缺少 reportId，无法加载综合报告'
      })
      return
    }

    this.setData({ reportId })
    this.loadReport(reportId)
  },

  retryLoad() {
    if (!this.data.reportId) {
      return
    }
    this.loadReport(this.data.reportId)
  },

  getUserId(): string | number | null {
    const app = getApp<IAppOption>()
    const globalData = app.globalData || {}

    if (globalData.userId) {
      return globalData.userId
    }

    const cachedUserId = wx.getStorageSync('USER_ID')
    if (cachedUserId) {
      return cachedUserId
    }

    const profile = wx.getStorageSync('USER_PROFILE')
    if (profile) {
      try {
        const profileData = typeof profile === 'string' ? JSON.parse(profile) : profile
        return profileData.userId || profileData.id || null
      } catch (error) {
        return null
      }
    }

    return null
  },

  async loadReport(reportId: string) {
    const userId = this.getUserId()
    if (!userId) {
      this.setData({
        loading: false,
        error: true,
        errorMessage: '请先登录后再查看综合报告'
      })
      return
    }

    this.setData({
      loading: true,
      error: false,
      errorMessage: '',
      report: {},
      reportBlocks: []
    })

    try {
      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/comprehensive-reports/detail?patientId=${encodeURIComponent(String(userId))}&reportId=${encodeURIComponent(reportId)}`,
          method: 'GET',
          success(res) {
            resolve(res)
          },
          fail(err) {
            reject(err)
          }
        })
      })

      const body = response.data || {}
      if (response.statusCode === 200 && body.success && body.data) {
        const data = body.data || {}
        const basis = data.basis || data.sourceInfo || {}
        const reportText = cleanReportText(data.reportText || data.report_text || '')
        const description = basis.description || basis.sourceNotice || ''

        this.setData({
          loading: false,
          error: false,
          errorMessage: '',
          report: {
            ...data,
            diseaseTypeName: data.diseaseTypeName || getDiseaseTypeName(data.diseaseType),
            title: data.title || '综合健康报告'
          },
          basis: {
            ...basis,
            description,
            diseaseTypeName: basis.diseaseTypeName || getDiseaseTypeName(basis.diseaseType || data.diseaseType),
            visitTypeName: basis.visitTypeName || getVisitTypeName(basis.visitType),
            questionnaireNames: Array.isArray(basis.questionnaireNames) ? basis.questionnaireNames : [],
            questionnaireRecordIds: Array.isArray(basis.questionnaireRecordIds) ? basis.questionnaireRecordIds : []
          },
          reportBlocks: this.buildReportBlocks(reportText)
        })
        return
      }

      const message = body.message || body.error || '综合报告加载失败'
      this.setData({
        loading: false,
        error: true,
        errorMessage: message
      })
    } catch (error) {
      console.error('[comprehensive-report] 加载失败:', error)
      this.setData({
        loading: false,
        error: true,
        errorMessage: '综合报告加载失败，请稍后重试'
      })
    }
  },

  buildReportBlocks(reportText: string): ReportBlock[] {
    const lines = String(reportText || '').split('\n')
    const blocks: ReportBlock[] = []

    lines.forEach((line) => {
      const text = String(line || '').trim()
      if (!text) {
        blocks.push({
          text: '',
          isHeading: false,
          isBlank: true
        })
        return
      }

      blocks.push({
        text,
        isHeading: /^[一二三四五六七八九十]+、/.test(text),
        isBlank: false
      })
    })

    return blocks
  }
})
