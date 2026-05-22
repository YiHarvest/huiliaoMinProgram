import {
  completePointsTask,
  getPointsDashboard,
  getPointsExchangeItem,
  redeemExchangeItem
} from '../../utils/points-store'

Page({
  data: {
    loading: true,
    itemId: '',
    currentPoints: 0,
    item: null as null | {
      id: string
      name: string
      points: number
      description: string
      tag: string
      highlight: string
    },
    gapPoints: 0,
    canRedeem: false,
    recommendedTasks: [] as Array<{
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
    successMessage: ''
  },

  onLoad(options: Record<string, string | undefined>) {
    const itemId = String(options.itemId || options.id || '').trim()
    this.setData({ itemId })
    this.refreshData()
  },

  onShow() {
    this.refreshData()
  },

  refreshData() {
    const dashboard = getPointsDashboard()
    const item = getPointsExchangeItem(this.data.itemId)

    if (!item) {
      this.setData({
        loading: false,
        item: null,
        currentPoints: dashboard.balance,
        gapPoints: 0,
        canRedeem: false,
        recommendedTasks: dashboard.tasks
      })
      return
    }

    this.setData({
      loading: false,
      currentPoints: dashboard.balance,
      item,
      gapPoints: Math.max(0, item.points - dashboard.balance),
      canRedeem: dashboard.balance >= item.points,
      recommendedTasks: dashboard.tasks,
      successMessage: ''
    })
  },

  onBackTap() {
    wx.navigateBack({
      delta: 1
    })
  },

  onRedeemTap() {
    if (!this.data.item) {
      return
    }

    if (!this.data.canRedeem) {
      wx.showToast({
        title: `还差 ${this.data.gapPoints} 积分`,
        icon: 'none'
      })
      return
    }

    wx.showModal({
      title: '确认兑换',
      content: `是否使用 ${this.data.item.points} 积分兑换 ${this.data.item.name}？`,
      confirmText: '立即兑换',
      cancelText: '再看看',
      success: (res) => {
        if (!res.confirm) {
          return
        }

        const result = redeemExchangeItem(this.data.item!.id)
        this.setData({
          currentPoints: result.balance,
          canRedeem: result.balance >= this.data.item!.points,
          gapPoints: Math.max(0, this.data.item!.points - result.balance),
          successMessage: result.success ? `兑换成功，已扣除 ${this.data.item!.points} 积分` : ''
        })

        wx.showToast({
          title: result.message,
          icon: result.success ? 'success' : 'none'
        })
      }
    })
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
      this.refreshData()
      return
    }

    if (route) {
      wx.navigateTo({
        url: route
      })
    }
  }
})
