import { expertProfiles } from '../../data/experts'

interface ExpertDetail {
  id: string
  name: string
  title: string
  department: string
  focus: string[]
  summary: string
  serviceLabel: string
  theme: string
  schedule: string
  details: {
    intro: string
    honors: string
    expertise: string
    schedule: {
      monday: string
      tuesday: string
      wednesday: string
      thursday: string
      friday: string
      saturday: string
      sunday: string
    }
  }
}

Page({
  data: {
    expert: null as ExpertDetail | null
  },
  onLoad(query: Record<string, string | undefined>) {
    const expertId = query.id as string
    
    if (expertId) {
      const expert = expertProfiles.find(e => e.id === expertId) as ExpertDetail
      if (expert) {
        this.setData({ expert })
        wx.setNavigationBarTitle({ title: `${expert.name}主任详情` })
      } else {
        wx.showToast({ title: '未找到专家信息', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 1000)
      }
    } else {
      wx.showToast({ title: '参数错误', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1000)
    }
  },
  onConsultAssistant() {
    const expert = this.data.expert
    if (expert && expert.id === 'chen-wangqiang') {
      wx.navigateTo({ url: '/pages/chen-agent/chen-agent?assistantId=chen' })
    } else {
      wx.navigateTo({ url: '/pages/chen-agent/chen-agent?assistantId=xiaohui' })
    }
  }
})
