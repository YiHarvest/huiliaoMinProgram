import { modeArticleMap } from '../../data/mode-articles'

Page({
  data: {
    article: null as unknown
  },
  onLoad(options?: Record<string, string | undefined>) {
    const id = options && options.id
    const article = id ? modeArticleMap[id] : undefined

    if (!article) {
      wx.showToast({
        title: '内容不存在',
        icon: 'none'
      })
      return
    }

    wx.setNavigationBarTitle({
      title: article.title
    })

    this.setData({
      article
    })
  },
  onBackHome() {
    wx.switchTab({
      url: '/pages/home/home'
    })
  },
  onAboutTap() {
    wx.switchTab({
      url: '/pages/mine/mine'
    })
  }
})
