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
    currentList: [] as DataItem[]
  },

  onLoad() {
    this.loadData('questionnaire')
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
        list = await this.loadComprehensiveData()
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
    return [
      {
        id: 'q-1',
        icon: '📝',
        title: '孕前健康评估量表',
        createdAt: '2026-04-29 14:20',
        score: 82,
        recordId: 'record-001'
      },
      {
        id: 'q-2',
        icon: '📝',
        title: '中医体质辨识量表',
        createdAt: '2026-04-28 09:35',
        score: 76,
        recordId: 'record-002'
      },
      {
        id: 'q-3',
        icon: '📝',
        title: '妇科健康评估量表',
        createdAt: '2026-04-25 16:48',
        score: 88,
        recordId: 'record-003'
      }
    ]
  },

  async loadTongueData(): Promise<DataItem[]> {
    return [
      {
        id: 't-1',
        icon: '👅',
        title: '舌苔分析记录',
        createdAt: '2026-04-29 10:15',
        summary: '舌质淡红，舌苔薄白，整体状态良好',
        analysisId: 'analysis-001'
      },
      {
        id: 't-2',
        icon: '👅',
        title: '舌苔分析记录',
        createdAt: '2026-04-26 15:30',
        summary: '舌质偏红，提示体内有轻微火气',
        analysisId: 'analysis-002'
      }
    ]
  },

  async loadReportData(): Promise<DataItem[]> {
    return [
      {
        id: 'r-1',
        icon: '📄',
        title: '体检报告',
        createdAt: '2026-04-27 11:20',
        type: '血常规检查',
        status: '已分析',
        reportId: 'report-001'
      },
      {
        id: 'r-2',
        icon: '📄',
        title: 'B超报告',
        createdAt: '2026-04-24 14:45',
        type: '妇科B超',
        status: '已分析',
        reportId: 'report-002'
      }
    ]
  },

  async loadComprehensiveData(): Promise<DataItem[]> {
    return [
      {
        id: 'mock-1',
        icon: '📊',
        title: '综合健康报告',
        createdAt: '2026-04-21 10:51'
      },
      {
        id: 'mock-2',
        icon: '📊',
        title: '综合健康报告',
        createdAt: '2026-04-20 18:04'
      }
    ]
  },

  handleView(e: WechatMiniprogram.TouchEvent) {
    const item = e.currentTarget.dataset.item as DataItem
    const tab = this.data.activeTab as TabKey

    if (!item) return

    if (tab === 'questionnaire') {
      if (item.recordId) {
        wx.navigateTo({
          url: `/pages/questionnaire/questionnaire?recordId=${item.recordId}`
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
      wx.showModal({
        title: '舌苔分析详情',
        content: item.summary || '暂无舌苔分析详情',
        showCancel: false
      })
      return
    }

    if (tab === 'report') {
      wx.showModal({
        title: '检查报告详情',
        content: `报告类型：${item.type || '未知'}\n状态：${item.status || '未知'}\n\n详细内容开发中`,
        showCancel: false
      })
      return
    }

    if (tab === 'comprehensive') {
      wx.showModal({
        title: '综合报告详情',
        content: '综合报告详情功能开发中，后续将从数据库读取完整报告内容。',
        showCancel: false
      })
    }
  }
})