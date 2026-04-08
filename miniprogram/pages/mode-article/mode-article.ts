import { modeArticleMap } from '../../data/mode-articles'

Component({
  data: {
    article: null as (typeof modeArticleMap)[string] | null
  },
  lifetimes: {
    attached() {
      const pages = getCurrentPages()
      const currentPage = pages[pages.length - 1]
      const id = currentPage?.options?.id
      const article = typeof id === 'string' ? modeArticleMap[id] : undefined

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
    }
  },
  methods: {
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
  }
})
