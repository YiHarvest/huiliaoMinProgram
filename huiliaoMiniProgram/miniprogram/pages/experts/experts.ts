import { expertProfiles } from '../../data/experts'

Component({
  data: {
    experts: expertProfiles
  },
  methods: {
    onConsultExpert(event: WechatMiniprogram.CustomEvent) {
      const name = event.currentTarget.dataset.name as string

      wx.showToast({
        title: `${name}服务待接入`,
        icon: 'none'
      })
    }
  }
})
