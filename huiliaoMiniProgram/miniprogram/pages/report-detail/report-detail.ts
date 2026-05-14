import { formatDisplayDate } from '../../utils/date'

interface ReportDetailFile {
  fileId?: number
  fileUrl?: string
  originalName?: string
  fileSize?: number
  mimeType?: string
  sortOrder?: number
  createdAt?: string
}

interface ReportDetailData {
  reportId?: number
  userId?: number
  doctorId?: string | null
  doctorName?: string
  doctorDepartment?: string
  reportType?: string
  status?: string
  remark?: string | null
  createdAt?: string
  updatedAt?: string
  files?: ReportDetailFile[]
}

type ReportDetailStatus = 'loading' | 'ready' | 'empty' | 'error'

const API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'

Page({
  data: {
    reportId: '',
    loading: false,
    error: false,
    status: 'loading' as ReportDetailStatus,
    statusText: '',
    report: null as ReportDetailData | null,
    fileUrls: [] as string[],
    createdAt: '',  // 单独存储格式化后的创建时间
    updatedAt: ''   // 单独存储格式化后的更新时间
  },

  onLoad(options: Record<string, string | undefined>) {
    const reportId = options.reportId ? decodeURIComponent(options.reportId) : ''
    if (!reportId) {
      this.setData({
        status: 'error',
        error: true,
        statusText: '报告ID无效'
      })
      return
    }

    this.setData({ reportId })
    wx.setNavigationBarTitle({ title: '检查报告' })
    this.loadDetail(reportId)
  },

  getUserId(): string | number | null {
    const app = getApp<IAppOption>()
    const globalData = app.globalData || {}

    if (globalData.userId) return globalData.userId
    const storedUserId = wx.getStorageSync('USER_ID')
    if (storedUserId) return storedUserId

    const profile = wx.getStorageSync('USER_PROFILE')
    if (profile) {
      const profileData = typeof profile === 'string' ? JSON.parse(profile) : profile
      return profileData.userId || profileData.id || null
    }

    return null
  },

  formatDate(value?: string | null): string {
    return formatDisplayDate(value || '')
  },

  formatStatus(status?: string): string {
    const map: Record<string, string> = {
      created: '创建中',
      uploaded: '已上传',
      completed: '已完成',
      analyzing: '分析中',
      analyzed: '已分析',
      deleted: '已删除'
    }
    return map[status || ''] || status || '未知'
  },

  async loadDetail(reportId: string) {
    const userId = this.getUserId()
    if (!userId) {
      this.setData({
        loading: false,
        error: true,
        status: 'error',
        statusText: '请先登录后查看检查报告'
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
          url: `${API_BASE_URL}/api/report/detail?reportId=${encodeURIComponent(reportId)}&userId=${encodeURIComponent(String(userId))}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      if (response.statusCode === 200 && response.data?.success) {
        const report = (response.data.data || {}) as ReportDetailData
        const files = Array.isArray(report.files) ? report.files : []
        const fileUrls = files.map((file) => file.fileUrl || '').filter(Boolean)

        this.setData({
          loading: false,
          error: false,
          status: files.length === 0 ? 'empty' : 'ready',
          statusText: files.length === 0 ? '该报告暂无图片' : '',
          report,
          fileUrls,
          // 参考 tongue-detail 的实现，单独格式化时间字段
          createdAt: this.formatDate(report.createdAt || ''),
          updatedAt: this.formatDate(report.updatedAt || '')
        })
      } else {
        throw new Error(response.data?.error || '加载检查报告失败')
      }
    } catch (error) {
      console.error('[report-detail] loadDetail failed:', error)
      this.setData({
        loading: false,
        error: true,
        status: 'error',
        statusText: '加载检查报告失败'
      })
    }
  },

  retryLoad() {
    if (this.data.reportId) {
      this.loadDetail(this.data.reportId)
    }
  },

  previewImage(e: WechatMiniprogram.TouchEvent) {
    const current = e.currentTarget.dataset.url as string
    if (!this.data.fileUrls.length) {
      return
    }

    wx.previewImage({
      urls: this.data.fileUrls,
      current: current || this.data.fileUrls[0]
    })
  },

  previewAll() {
    if (!this.data.fileUrls.length) return

    wx.previewImage({
      urls: this.data.fileUrls,
      current: this.data.fileUrls[0]
    })
  }
})
