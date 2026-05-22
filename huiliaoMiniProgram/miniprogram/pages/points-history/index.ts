import {
  formatPointsDelta,
  getPointsHistoryRecords,
  getPointsStateSnapshot,
  getPointsTimelineLabel
} from '../../utils/points-store'

Page({
  data: {
    balance: 0,
    todayEarned: 0,
    weeklyEarned: 0,
    history: [] as Array<{
      id: string
      type: 'get' | 'spend'
      source: string
      title: string
      delta: number
      note: string
      createdAt: string
      sourceLabel: string
      deltaText: string
      deltaClass: string
    }>
  },

  onShow() {
    this.refreshData()
  },

  refreshData() {
    const state = getPointsStateSnapshot()
    const history = getPointsHistoryRecords().map((item) => ({
      ...item,
      sourceLabel: getPointsTimelineLabel(item.source),
      deltaText: formatPointsDelta(item.delta),
      deltaClass: item.delta >= 0 ? 'history-delta--get' : 'history-delta--spend'
    }))

    this.setData({
      balance: state.balance,
      todayEarned: state.todayEarned,
      weeklyEarned: state.weeklyEarned,
      history
    })
  },

  onBackTap() {
    wx.navigateBack({
      delta: 1
    })
  }
})
