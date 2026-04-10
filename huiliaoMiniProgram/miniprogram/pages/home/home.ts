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
        iconType: 'clipboard',
        title: '填写量表',
        desc: '专科状况分析',
        route: '/pages/scale-form/scale-form'
      },
      {
        iconType: 'tongue',
        title: '舌苔上传',
        desc: '中医体质辨识',
        route: '/pages/tongue-upload/tongue-upload'
      },
      {
        iconType: 'report',
        title: '上传报告',
        desc: '检查报告分析',
        route: '/pages/report-upload/report-upload'
      },
      {
        iconType: 'profile',
        title: '综合报告',
        desc: '查看综合结果',
        route: '/pages/comprehensive-report/comprehensive-report'
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
    onOpenFeature(event: WechatMiniprogram.CustomEvent) {
      const { route, title } = event.currentTarget.dataset as {
        route?: string
        title: string
      }

      if (route) {
        wx.navigateTo({
          url: route
        })
        return
      }

      wx.showToast({
        title: `${title}功能待接入`,
        icon: 'none'
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
