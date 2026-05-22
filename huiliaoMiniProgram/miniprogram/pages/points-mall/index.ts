import {
  completePointsSignIn,
  completePointsTask,
  getPointsDashboard,
  getPointsStateSnapshot
} from '../../utils/points-store'

Page({
  data: {
    loading: false,
    currentPoints: 0,
    todayEarned: 0,
    weeklyEarned: 0,
    signInDays: 0,
    initType: 'new',
    initBonus: 0,
    initBreakdown: [] as Array<{ label: string; points: number }>,
    dailyLimitRemaining: 0,
    weeklyLimitRemaining: 0,
    historyCount: 0,
    signInDaysView: [] as Array<{ day: number; points: number; active: boolean; today: boolean; completed: boolean }>,
    tasks: [] as Array<{
      id: string
      title: string
      desc: string
      points: number
      route?: string
      actionText: string
      claimed: boolean
      claimableToday: boolean
      note: string
    }>,
    exchangeItems: [] as Array<{
      id: string
      name: string
      points: number
      description: string
      tag: string
      highlight: string
    }>,
    signInButtonText: '立即签到',
    signInButtonDisabled: false,
    initBadgeText: '新手积分',
    initSummaryText: ''
  },

  onLoad() {
    this.refreshDashboard()
  },

  onShow() {
    this.refreshDashboard()
  },

  refreshDashboard() {
    const dashboard = getPointsDashboard()
    const snapshot = getPointsStateSnapshot()
    const hasSignedToday = snapshot.signInDate === this.getTodayKey()

    this.setData({
      currentPoints: dashboard.balance,
      todayEarned: dashboard.todayEarned,
      weeklyEarned: dashboard.weeklyEarned,
      signInDays: dashboard.signInDays,
      initType: dashboard.initType,
      initBonus: dashboard.initBonus,
      initBreakdown: dashboard.initBreakdown,
      dailyLimitRemaining: dashboard.dailyLimitRemaining,
      weeklyLimitRemaining: dashboard.weeklyLimitRemaining,
      historyCount: dashboard.historyCount,
      signInDaysView: dashboard.signInDaysView,
      tasks: dashboard.tasks,
      exchangeItems: dashboard.exchangeItems,
      signInButtonText: hasSignedToday ? '今日已签到' : '立即签到',
      signInButtonDisabled: hasSignedToday,
      initBadgeText: dashboard.initType === 'old' ? '上线体验积分' : '新手积分',
      initSummaryText: dashboard.initBreakdown
        .map((item) => `${item.label} +${item.points}`)
        .join(' · ')
    })
  },

  getTodayKey() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  },

  onOpenHistory() {
    wx.navigateTo({
      url: '/pages/points-history/index'
    })
  },

  onOpenGame() {
    wx.navigateTo({
      url: '/pages/points-game/index'
    })
  },

  onSignInTap() {
    if (this.data.signInButtonDisabled) {
      wx.showToast({
        title: '今天已经签到过了',
        icon: 'none'
      })
      return
    }

    const result = completePointsSignIn()
    wx.showToast({
      title: result.message,
      icon: result.success ? 'success' : 'none'
    })
    this.refreshDashboard()
  },

  onTaskTap(event: WechatMiniprogram.CustomEvent) {
    const { taskId, route } = event.currentTarget.dataset as {
      taskId?: string
      route?: string
    }

    if (!taskId) {
      return
    }

    if (taskId === 'view_rules') {
      const result = completePointsTask('view_rules')
      wx.showToast({
        title: result.message,
        icon: result.success ? 'success' : 'none'
      })
      this.refreshDashboard()
      return
    }

    if (route) {
      wx.navigateTo({
        url: route
      })
    }
  },

  onExchangeTap(event: WechatMiniprogram.CustomEvent) {
    const { itemId } = event.currentTarget.dataset as { itemId?: string }
    if (!itemId) {
      return
    }

    wx.navigateTo({
      url: `/pages/points-exchange/index?itemId=${encodeURIComponent(itemId)}`
    })
  }
})
