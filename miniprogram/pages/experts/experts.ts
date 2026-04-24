import { expertProfiles } from '../../data/experts'

Component({
  data: {
    experts: expertProfiles
  },
  methods: {
    onExpertCardTap(event: WechatMiniprogram.CustomEvent) {
      const id = event.currentTarget.dataset.id as string
      
      // 跳转到专家详情页面
      wx.navigateTo({
        url: `/pages/expert-detail/expert-detail?id=${id}`
      })
    },
    onConsultExpert(event: WechatMiniprogram.CustomEvent) {
      const id = event.currentTarget.dataset.id as string
      
      // 根据专家id跳转到对应智能体的工作台
      if (id === 'chen-wangqiang') {
        wx.navigateTo({
          url: '/pages/workbench/workbench?assistantId=chen'
        })
      } else {
        wx.navigateTo({
          url: '/pages/workbench/workbench?assistantId=xiaohui'
        })
      }
    }
  }
})
