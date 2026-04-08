import { modeArticles } from '../../data/mode-articles'

Component({
  data: {
    currentBanner: 0,
    bannerList: [
      {
        id: 1,
        kicker: '医疗科技',
        title: 'AI赋能医疗专家',
        subtitle: '安全专属的数字合伙人',
        tags: ['安全合规', '深度赋能'],
        image: '/assets/home-banner-hero-cropped.png'
      },
      {
        id: 2,
        kicker: '患者管理',
        title: '全周期服务更高效',
        subtitle: '从诊前到诊后，持续连接患者',
        tags: ['患者连接', '持续服务'],
        image: '/assets/home-banner-hero-cropped.png'
      },
      {
        id: 3,
        kicker: '知识沉淀',
        title: '让专家经验可复制',
        subtitle: '把临床经验沉淀为长期服务资产',
        tags: ['知识资产', '数据洞察'],
        image: '/assets/home-banner-hero-cropped.png'
      }
    ],
    featureGrid: [
      {
        iconType: 'ai',
        title: 'AI辅助',
        desc: '医生服务智能支持'
      },
      {
        iconType: 'monitor',
        title: '健康监测',
        desc: '提升患者管理效率'
      },
      {
        iconType: 'pill',
        title: '用药管理',
        desc: '持续提醒与跟进'
      },
      {
        iconType: 'chart',
        title: '数据分析',
        desc: '形成可视化结果分析'
      }
    ],
    modeEntries: modeArticles.map((article) => ({
      id: article.id,
      tag: article.cardTag,
      title: article.cardTitle,
      summary: article.cardSummary
    }))
  },
  methods: {
    onSwiperChange(event: WechatMiniprogram.CustomEvent) {
      this.setData({
        currentBanner: event.detail.current
      })
    },
    onOpenModeArticle(event: WechatMiniprogram.CustomEvent) {
      const id = event.currentTarget.dataset.id as string
      wx.navigateTo({
        url: `/pages/mode-article/mode-article?id=${id}`
      })
    },
    onLearnMoreTap() {
      wx.navigateTo({
        url: '/pages/mode-article/mode-article?id=hospital-system'
      })
    },
    onAboutTap() {
      wx.switchTab({
        url: '/pages/mine/mine'
      })
    }
  }
})
