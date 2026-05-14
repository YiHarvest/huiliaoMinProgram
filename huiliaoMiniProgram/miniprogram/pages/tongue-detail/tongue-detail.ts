const API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'

import { formatDisplayDate } from '../../utils/date'

interface TongueDetailReport {
  analysisId?: string
  overall?: {
    subject?: string
    score?: number
    summary?: string
    riskWarnings?: string[]
  }
  healthSuggestions?: {
    diet?: Array<{ name?: string; effect?: string }>
    exercise?: string
    physicalTherapy?: string
  }
  tongueAnalysis?: {
    summary?: string
    tongueColor?: Array<{ description?: string }>
    tongueShape?: Array<{ description?: string }>
    coatingTexture?: Array<{ description?: string }>
    coatingColor?: Array<{ description?: string }>
  }
  faceAnalysis?: {
    summary?: string
  }
  healthAnalysis?: {
    subjectName?: string
    subjectFeature?: string
    subjectOutline?: string
    dietAccept?: string
    dietReject?: string
    exerciseAccept?: string
    exerciseReject?: string
    physicalPosition?: string
    physicalSearch?: string
    physicalOperation?: string
  }
  basicInfo?: {
    sex?: string
    age?: string | number
  }
}

type TongueDetailStatus = 'loading' | 'ready' | 'empty' | 'error'

Page({
  data: {
    analysisId: '',
    loading: false,
    error: false,
    report: null as TongueDetailReport | null,
    createdAt: '',
    updatedAt: '',
    statusText: '',
    status: 'loading' as TongueDetailStatus
  },

  onLoad(options: Record<string, string | undefined>) {
    const analysisId = options.analysisId ? decodeURIComponent(options.analysisId) : ''
    if (!analysisId) {
      this.setData({
        status: 'error',
        error: true,
        statusText: '分析记录ID无效'
      })
      return
    }

    this.setData({
      analysisId
    })

    wx.setNavigationBarTitle({
      title: '舌苔分析'
    })

    this.loadDetail(analysisId)
  },

  getUserId(): string | number | null {
    const app = getApp<IAppOption>()
    const globalData = app.globalData || {}

    let userId: string | number | null = null
    if (globalData.userId) {
      userId = globalData.userId
    } else if (wx.getStorageSync('USER_ID')) {
      userId = wx.getStorageSync('USER_ID')
    } else {
      const profile = wx.getStorageSync('USER_PROFILE')
      if (profile) {
        const profileData = typeof profile === 'string' ? JSON.parse(profile) : profile
        userId = profileData.userId || profileData.id
      }
    }

    return userId
  },

  formatDate(value?: string | null): string {
    return formatDisplayDate(value || '')
  },

  async loadDetail(analysisId: string) {
    const userId = this.getUserId()
    if (!userId) {
      this.setData({
        loading: false,
        error: true,
        status: 'error',
        statusText: '请先登录后查看舌苔分析'
      })
      return
    }

    this.setData({
      loading: true,
      error: false,
      status: 'loading',
      statusText: '加载中...'
    })

    try {
      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/tongue/detail?analysisId=${encodeURIComponent(analysisId)}&userId=${encodeURIComponent(String(userId))}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      if (response.statusCode === 200 && response.data?.success) {
        const detail = response.data.data || {}
        const report = detail.report || null
        if (!report) {
          this.setData({
            loading: false,
            error: false,
            status: 'empty',
            statusText: '暂无可展示的分析结果',
            report: null,
            createdAt: '',
            updatedAt: ''
          })
          return
        }

        this.setData({
          loading: false,
          error: false,
          status: 'ready',
          statusText: '',
          report,
          createdAt: this.formatDate(detail.createdAt),
          updatedAt: this.formatDate(detail.updatedAt)
        })
      } else {
        throw new Error(response.data?.error || '加载舌苔分析失败')
      }
    } catch (error) {
      console.error('[tongue-detail] loadDetail failed:', error)
      this.setData({
        loading: false,
        error: true,
        status: 'error',
        statusText: '加载舌苔分析失败',
        createdAt: '',
        updatedAt: ''
      })
    }
  },

  retryLoad() {
    if (this.data.analysisId) {
      this.loadDetail(this.data.analysisId)
    }
  },

  formatList(items?: Array<{ description?: string }>): string[] {
    return (items || []).map((item) => item.description || '').filter(Boolean)
  }
})
