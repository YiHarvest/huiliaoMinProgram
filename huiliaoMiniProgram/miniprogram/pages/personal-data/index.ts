import { formatDisplayDate } from '../../utils/date'

type TabKey = 'questionnaire' | 'tongue' | 'report' | 'comprehensive'

interface DataItem {
  id: string
  title: string
  createdAt: string
  icon: string
  score?: number
  recordId?: string
  summary?: string
  analysisId?: string
  type?: string
  status?: string
  reportId?: string
  doctorName?: string
  doctorDepartment?: string
  uiState?: 'normal' | 'deleting'
}

const API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'

function cleanDisplayText(value: unknown): string {
  return String(value || '')
    .replace(/\*\*/g, '')
    .replace(/```/g, '')
    .replace(/^\s*#+\s*/gm, '')
    .trim()
}

function getComprehensiveDiseaseTypeName(value: unknown): string {
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

Page({
  data: {
    tabs: [
      { key: 'questionnaire', label: '量表记录' },
      { key: 'tongue', label: '舌苔记录' },
      { key: 'report', label: '检查报告' },
      { key: 'comprehensive', label: '综合报告' }
    ],
    activeTab: 'questionnaire' as TabKey,
    loading: false,
    error: false,
    emptyText: '暂无量表记录',
    currentList: [] as DataItem[],
    suppressTapUntil: 0,
    comprehensiveGenerating: false
  },

  onLoad() {
    // 检查是否有默认 tab 设置
    const defaultTab = wx.getStorageSync('DATA_DEFAULT_TAB') as TabKey
    if (defaultTab && ['questionnaire', 'tongue', 'report', 'comprehensive'].includes(defaultTab)) {
      this.setData({ activeTab: defaultTab })
      this.loadData(defaultTab)
      // 清除默认 tab 设置
      wx.removeStorageSync('DATA_DEFAULT_TAB')
    } else {
      this.loadData('questionnaire')
    }
  },

  onShow() {
    // 页面显示时重新加载当前 tab 数据
    this.loadData(this.data.activeTab)
  },

  switchTab(e: WechatMiniprogram.TouchEvent) {
    const tab = e.currentTarget.dataset.tab as TabKey
    if (!tab || tab === this.data.activeTab) return

    this.setData({
      activeTab: tab,
      loading: true,
      error: false,
      currentList: [],
      emptyText: this.getEmptyText(tab)
    })

    this.loadData(tab)
  },

  retryLoad() {
    this.loadData(this.data.activeTab)
  },

  refreshReportListSilently() {
    if (this.data.activeTab !== 'report') {
      return
    }

    this.loadReportData()
      .then((list) => {
        if (this.data.activeTab === 'report') {
          this.setData({
            currentList: list,
            error: false,
            emptyText: this.getEmptyText('report')
          })
        }
      })
      .catch((error) => {
        console.error('[personal-data] 删除后刷新检查报告失败:', error)
      })
  },

  getEmptyText(tab: TabKey): string {
    const texts: Record<TabKey, string> = {
      questionnaire: '暂无量表记录',
      tongue: '暂无舌苔记录',
      report: '暂无检查报告',
      comprehensive: '暂无综合报告'
    }
    return texts[tab]
  },

  async loadData(tab: TabKey) {
    this.setData({
      loading: true,
      error: false,
      emptyText: this.getEmptyText(tab)
    })

    try {
      let list: DataItem[] = []

      if (tab === 'questionnaire') {
        list = await this.loadQuestionnaireData()
      } else if (tab === 'tongue') {
        list = await this.loadTongueData()
      } else if (tab === 'report') {
        list = await this.loadReportData()
      } else if (tab === 'comprehensive') {
        list = await this.loadComprehensiveDataFromApi()
      }

      this.setData({
        loading: false,
        currentList: list
      })
    } catch (err) {
      console.error('加载个人数据失败：', err)
      this.setData({
        loading: false,
        error: true,
        currentList: []
      })
    }
  },

  async loadQuestionnaireData(): Promise<DataItem[]> {
    try {
      const userId = this.getUserId()
      if (!userId) {
        console.warn('[personal-data] 未找到 userId，无法加载量表记录')
        return []
      }

      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/questionnaires/records?userId=${userId}&limit=50`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      if (response.statusCode === 200 && response.data?.success) {
        const list = response.data.data?.list || []
        return list.map((item: any, index: number) => ({
          id: String(item.recordId || item.id || index),
          icon: '📝',
          title: item.title || item.questionnaireName || '量表记录',
          createdAt: this.formatDate(item.createdAt),
          summary: cleanDisplayText(item.summary || item.analysisText || ''),
          recordId: String(item.recordId || ''),
          status: '已保存'
        }))
      }

      console.error('[personal-data] 加载量表记录失败:', response.data?.error)
      return []
    } catch (error) {
      console.error('[personal-data] 加载量表记录异常:', error)
      return []
    }
  },

  async loadTongueData(): Promise<DataItem[]> {
    try {
      const userId = this.getUserId()
      if (!userId) {
        console.warn('[personal-data] 未找到 userId，无法加载舌苔记录')
        return []
      }

      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/tongue/list?userId=${userId}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      if (response.statusCode === 200 && response.data?.success) {
        const list = response.data.data?.list || []
        return list.map((item: any, index: number) => ({
          id: String(item.analysisId || item.id || index),
          icon: '👅',
          title: item.title || item.subject || '舌苔分析记录',
          createdAt: this.formatDate(item.createdAt),
          summary: item.summary || item.report?.overall?.summary || '',
          analysisId: String(item.analysisId || item.id || ''),
          status: this.formatTongueStatus(item.status)
        }))
      }

      console.error('[personal-data] 加载舌苔记录失败:', response.data?.error)
      return []
    } catch (error) {
      console.error('[personal-data] 加载舌苔记录异常:', error)
      return []
    }
  },

  async loadReportData(): Promise<DataItem[]> {
    try {
      // 获取 userId
      const userId = this.getUserId()
      if (!userId) {
        console.warn('[personal-data] 未找到 userId，无法加载检查报告')
        return []
      }

      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/report/list?userId=${userId}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      if (response.statusCode === 200 && response.data?.success) {
        const reports = response.data.data?.list || []
        
        return reports.map((report: any) => {
          let displayTitle = '检查报告'

          if (report.reportType && report.reportType !== '检查报告') {
            if (report.remark && report.remark.trim()) {
              displayTitle = `${report.reportType}｜${report.remark.trim()}`
            } else {
              displayTitle = `${report.reportType}报告`
            }
          } else if (report.firstFileName) {
            let fileName = report.firstFileName.replace(/\.[^/.]+$/, '')
            if (fileName.length > 15) {
              fileName = fileName.substring(0, 15) + '...'
            }
            displayTitle = fileName
          } else if (report.reportType) {
            displayTitle = report.reportType
          } else {
            const shortId = String(report.reportId || '').slice(-4)
            displayTitle = `检查报告 #${shortId}`
          }

          return {
            id: String(report.reportId),
            icon: '📄',
            title: displayTitle,
            createdAt: this.formatDate(report.createdAt),
            type: report.doctorDepartment || '',
            status: this.formatReportStatus(report.status),
            reportId: String(report.reportId),
            doctorName: report.doctorName || '',
            doctorDepartment: report.doctorDepartment || '',
            fileCount: report.fileCount || 0,
            firstFileUrl: report.firstFileUrl || null
          }
        })
      } else {
        console.error('[personal-data] 加载检查报告失败:', response.data?.error)
        return []
      }
    } catch (error) {
      console.error('[personal-data] 加载检查报告异常:', error)
      return []
    }
  },

  getUserId(): string | number | null {
    const app = getApp<IAppOption>()
    const globalData = app.globalData || {}
    
    // 尝试从多个来源获取 userId
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

  formatDate(dateStr: string): string {
    return formatDisplayDate(dateStr)
  },

  formatReportStatus(status: string): string {
    const statusMap: Record<string, string> = {
      'created': '创建中',
      'uploaded': '已上传',
      'completed': '已完成',
      'analyzing': '分析中',
      'analyzed': '已分析'
    }
    return statusMap[status] || status || '未知'
  },

  formatTongueStatus(status: string): string {
    const statusMap: Record<string, string> = {
      'processing': '分析中',
      'completed': '已完成',
      'failed': '失败',
      'deleted': '已删除'
    }
    return statusMap[status] || status || '未知'
  },

  formatComprehensiveStatus(status: string): string {
    const statusMap: Record<string, string> = {
      completed: '已完成',
      failed: '生成失败',
      generating: '生成中',
      pending: '待生成'
    }
    return statusMap[status] || status || '未知'
  },

  async loadComprehensiveDataFromApi(): Promise<DataItem[]> {
    try {
      const userId = this.getUserId()
      if (!userId) {
        console.warn('[personal-data] 未找到 userId，无法加载综合报告')
        return []
      }

      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/comprehensive-reports?patientId=${userId}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      const body = response.data || {}
      if (response.statusCode === 200 && body?.success) {
        const list = body.data?.list || []
        return list.map((item: any, index: number) => ({
          id: String(item.reportId || index),
          icon: '🎯',
          title: item.title || '综合健康报告',
          createdAt: this.formatDate(item.createdAt),
          summary: '',
          reportId: String(item.reportId || ''),
          doctorName: item.doctorName || '',
          type: item.diseaseTypeName || getComprehensiveDiseaseTypeName(item.diseaseType),
          status: this.formatComprehensiveStatus(item.status)
        }))
      }

      console.error('[personal-data] 加载综合报告失败:', body?.message || body?.error || 'unknown error')
      return []
    } catch (error) {
      console.error('[personal-data] 加载综合报告异常:', error)
      return []
    }
  },

  async handleGenerateComprehensiveReportClean() {
    if (this.data.comprehensiveGenerating) {
      return
    }

    const userId = this.getUserId()
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }

    this.setData({ comprehensiveGenerating: true })

    const finish = () => {
      this.setData({ comprehensiveGenerating: false })
    }

    try {
      const previewResponse: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/comprehensive-reports/source-preview?patientId=${userId}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      const previewBody = previewResponse.data || {}
      const previewData = previewBody.data || {}
      if (previewResponse.statusCode !== 200 || previewBody.success === false || previewData.canGenerate === false) {
        wx.showModal({
          title: '暂无法生成综合报告',
          content: previewBody.message || '当前医生、疾病类型和初诊/复诊对应的量表尚未填写完整，或暂未找到最新舌苔记录。',
          showCancel: false
        })
        finish()
        return
      }

      const sourceBasis = previewData.sourceBasis || {}
      const questionnaireNames = Array.isArray(previewData.questionnaireNames)
        ? previewData.questionnaireNames
        : Array.isArray(sourceBasis.questionnaireNames)
          ? sourceBasis.questionnaireNames
          : []
      const diseaseTypeName = previewData.diseaseTypeName || sourceBasis.diseaseTypeName || getComprehensiveDiseaseTypeName(previewData.diseaseType || sourceBasis.diseaseType)
      const visitTypeName = sourceBasis.visitTypeName || (previewData.visitType === 'first' ? '初诊' : previewData.visitType === 'followup' ? '复诊' : previewData.visitType === 'referral' ? '转诊' : '未填写')

      const previewContent = [
        `量表来源：${sourceBasis.scaleSource || '当前医生、疾病类型和初诊/复诊对应量表组'}`,
        `具体量表：${questionnaireNames.length ? questionnaireNames.join('、') : '暂无'}`,
        `医生：${previewData.doctorName || sourceBasis.doctorName || ''}`,
        `疾病类型：${diseaseTypeName || ''}`,
        `就诊类型：${visitTypeName || ''}`,
        `量表填写时间：${previewData.questionnaireCompletedAt || sourceBasis.questionnaireCompletedAt || ''}`,
        `舌苔来源：${sourceBasis.tongueSource || '最新一次舌苔记录'}`,
        `舌苔时间：${previewData.tongueCreatedAt || sourceBasis.tongueCreatedAt || ''}`,
        `说明：${sourceBasis.description || '本报告基于以上信息生成，仅供健康信息整理和医生沟通参考。'}`
      ].join('\n')

      wx.showModal({
        title: '生成综合报告',
        content: previewContent,
        confirmText: '确认生成',
        cancelText: '取消',
        success: async (modalRes) => {
          if (!modalRes.confirm) {
            finish()
            return
          }

          try {
            const generateResponse: any = await new Promise((resolve, reject) => {
              wx.request({
                url: `${API_BASE_URL}/api/comprehensive-reports/generate`,
                method: 'POST',
                header: { 'Content-Type': 'application/json' },
                data: { patientId: String(userId) },
                success(res) { resolve(res) },
                fail(err) { reject(err) }
              })
            })

            const generateBody = generateResponse.data || {}
            if (generateResponse.statusCode === 200 && generateBody.success) {
              wx.showToast({ title: '生成成功', icon: 'success' })
              const reportId = generateBody.data?.reportId || ''
              const refreshedList = await this.loadComprehensiveDataFromApi()
              this.setData({
                currentList: refreshedList,
                error: false,
                emptyText: this.getEmptyText('comprehensive')
              })
              if (reportId) {
                wx.navigateTo({
                  url: `/pages/comprehensive-report/comprehensive-report?reportId=${encodeURIComponent(reportId)}`
                })
              }
            } else {
              wx.showModal({
                title: '生成失败',
                content: generateBody.message || '综合报告生成失败，请稍后重试。',
                showCancel: false
              })
            }
          } catch (error) {
            console.error('[personal-data] generate comprehensive report failed:', error)
            wx.showModal({
              title: '生成失败',
              content: '综合报告生成失败，请稍后重试。',
              showCancel: false
            })
          } finally {
            finish()
          }
        }
      })
    } catch (error) {
      console.error('[personal-data] preview comprehensive report failed:', error)
      finish()
      wx.showModal({
        title: '生成失败',
        content: '综合报告生成失败，请稍后重试。',
        showCancel: false
      })
    }
  },

  handleView(e: WechatMiniprogram.TouchEvent) {
    const item = e.currentTarget.dataset.item as DataItem
    const tab = this.data.activeTab as TabKey

    if (!item) return

    if (tab === 'report') {
      const reportId = item.reportId || item.id
      if (reportId && Date.now() < (this.data.suppressTapUntil || 0)) {
        return
      }

      if (item.uiState === 'deleting') {
        return
      }
    }

    if (tab === 'questionnaire') {
      if (item.recordId) {
        wx.navigateTo({
          url: `/pages/scale-result/scale-result?recordId=${item.recordId}&title=${encodeURIComponent(item.title || '')}`
        })
      } else {
        wx.showToast({
          title: '暂无量表详情',
          icon: 'none'
        })
      }
      return
    }

    if (tab === 'tongue') {
      if (item.analysisId) {
        wx.navigateTo({
          url: `/pages/tongue-detail/tongue-detail?analysisId=${encodeURIComponent(item.analysisId)}`
        })
      } else {
        wx.showModal({
          title: '舌苔分析详情',
          content: item.summary || '暂无舌苔分析详情',
          showCancel: false
        })
      }
      return
    }

    if (tab === 'report') {
      const reportId = item.reportId || item.id
      if (reportId) {
        wx.navigateTo({
          url: `/pages/report-detail/report-detail?reportId=${encodeURIComponent(reportId)}`
        })
      } else {
        wx.showToast({
          title: '报告ID无效',
          icon: 'none'
        })
      }
      return
    }

    if (tab === 'comprehensive') {
      const reportId = item.reportId || item.id
      if (reportId) {
        wx.navigateTo({
          url: `/pages/comprehensive-report/comprehensive-report?reportId=${encodeURIComponent(reportId)}`
        })
      } else {
        wx.showToast({
          title: '报告ID无效',
          icon: 'none'
        })
      }
    }
  },

  handleCardLongPress(e: WechatMiniprogram.TouchEvent) {
    const item = e.currentTarget.dataset.item as DataItem
    const tab = this.data.activeTab as TabKey

    if (tab !== 'report' || !item) {
      return
    }

    const reportId = item.reportId || item.id
    if (!reportId || item.uiState === 'deleting') {
      return
    }

    this.setData({
      suppressTapUntil: Date.now() + 1200
    })

    wx.showActionSheet({
      itemList: ['删除报告'],
      success: (res) => {
        if (res.tapIndex === 0) {
          this.confirmDeleteReport(item)
        }
      }
    })
  },

  confirmDeleteReport(item: DataItem) {
    const reportId = item.reportId || item.id
    if (!reportId) {
      return
    }

    wx.showModal({
      title: '删除确认',
      content: `确定要删除“${item.title}”吗？删除后将从列表中移除，且无法在当前列表中恢复。`,
      confirmText: '删除',
      confirmColor: '#E54D42',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          this.deleteReport(reportId)
        }
      }
    })
  },

  async deleteReport(reportId: string) {
    const userId = this.getUserId()
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }

    const nextList = this.data.currentList.map((item) => {
      if ((item.reportId || item.id) === reportId) {
        return {
          ...item,
          uiState: 'deleting' as const
        }
      }
      return item
    })

    this.setData({
      currentList: nextList,
      suppressTapUntil: Date.now() + 1200
    })

    try {
      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/report/delete`,
          method: 'POST',
          header: { 'Content-Type': 'application/json' },
          data: {
            reportId,
            userId
          },
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      if (response.statusCode === 200 && response.data?.success) {
        wx.showToast({
          title: '删除成功',
          icon: 'success'
        })

        setTimeout(() => {
          const filteredList = this.data.currentList.filter((item) => (item.reportId || item.id) !== reportId)

          this.setData({
            currentList: filteredList
          })

          this.refreshReportListSilently()
        }, 280)
      } else {
        throw new Error(response.data?.error || '删除失败')
      }
    } catch (error) {
      console.error('[personal-data] 删除报告失败:', error)
      this.setData({
        currentList: this.data.currentList.map((item) => {
          if ((item.reportId || item.id) === reportId) {
            return {
              ...item,
              uiState: 'normal' as const
            }
          }
          return item
        })
      })
      wx.showToast({
        title: '删除失败，请重试',
        icon: 'none'
      })
    }
  },

  async loadReportDetail(reportId: string) {
    if (!reportId) {
      wx.showToast({ title: '报告ID无效', icon: 'none' })
      return
    }

    const userId = this.getUserId()
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }

    wx.showLoading({ title: '加载中...' })

    try {
      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/report/detail?reportId=${reportId}&userId=${userId}`,
          method: 'GET',
          success(res) { resolve(res) },
          fail(err) { reject(err) }
        })
      })

      wx.hideLoading()

      if (response.statusCode === 200 && response.data?.success) {
        const report = response.data.data
        const files = report.files || []

        if (files.length === 0) {
          wx.showModal({
            title: '检查报告',
            content: `报告类型：${report.reportType || '未知'}\n医生：${report.doctorName || '未知'}\n科室：${report.doctorDepartment || '未知'}\n状态：${this.formatReportStatus(report.status)}\n\n暂无图片`,
            showCancel: false
          })
          return
        }

        // 提取图片 URL
        const imageUrls = files.map((f: any) => f.fileUrl).filter(Boolean)

        if (imageUrls.length > 0) {
          // 使用 wx.previewImage 预览图片
          wx.previewImage({
            urls: imageUrls,
            current: imageUrls[0]
          })
        }
      } else {
        wx.showToast({
          title: response.data?.error || '加载报告详情失败',
          icon: 'none'
        })
      }
    } catch (error) {
      wx.hideLoading()
      console.error('[personal-data] 加载报告详情异常:', error)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  }
})
