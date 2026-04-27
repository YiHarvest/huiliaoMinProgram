import { getSubscribeConfig, handleSubscribeAuthorization, showSubscribeGuide } from '../../utils/subscribe'

type SubscribeScene = 'ai_reply' | 'tongue_result' | 'appointment_reminder'

type SubscribeConfig = {
  scene: SubscribeScene
  name: string
  description: string
  templateId: string
  page: string
  enabled: boolean
}

type SubscriptionStatus = {
  scene: SubscribeScene
  name: string
  description: string
  enabled: boolean
  subscribed: boolean
}

Page({
  data: {
    configured: false,
    subscriptions: [] as SubscriptionStatus[],
    openid: '',
    isLoading: true,
    canSubscribeAny: false
  },

  onLoad() {
    this.loadConfig()
  },

  async loadConfig() {
    try {
      const config = await getSubscribeConfig()
      
      const subscriptions: SubscriptionStatus[] = config.scenes.map(scene => ({
        scene: scene.scene,
        name: scene.name,
        description: scene.description,
        enabled: scene.enabled,
        subscribed: false
      }))

      const canSubscribeAny = subscriptions.some(s => s.enabled && !s.subscribed)

      this.setData({
        configured: config.configured,
        subscriptions,
        canSubscribeAny,
        isLoading: false
      })
    } catch (error) {
      console.error('加载配置失败:', error)
      this.setData({
        isLoading: false
      })
      wx.showToast({
        title: '加载配置失败',
        icon: 'none'
      })
    }
  },

  async onSubscribeAll() {
    const openid = this.data.openid
    
    if (!openid) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }

    const enabledScenes = this.data.subscriptions
      .filter(s => s.enabled)
      .map(s => s.scene)

    if (enabledScenes.length === 0) {
      wx.showToast({
        title: '没有可订阅的消息类型',
        icon: 'none'
      })
      return
    }

    const result = await handleSubscribeAuthorization(openid, enabledScenes)
    
    if (result.success) {
      const updatedSubscriptions = this.data.subscriptions.map(s => ({
        ...s,
        subscribed: result.subscribedScenes.includes(s.scene)
      }))
      const canSubscribeAny = updatedSubscriptions.some(s => s.enabled && !s.subscribed)
      
      this.setData({
        subscriptions: updatedSubscriptions,
        canSubscribeAny
      })
    }
  },

  async onSubscribeScene(event: WechatMiniprogram.CustomEvent) {
    const scene = event.currentTarget.dataset.scene as SubscribeScene
    const openid = this.data.openid
    
    if (!openid) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }

    const result = await handleSubscribeAuthorization(openid, [scene])
    
    if (result.success) {
      const updatedSubscriptions = this.data.subscriptions.map(s => ({
        ...s,
        subscribed: s.scene === scene ? true : s.subscribed
      }))
      const canSubscribeAny = updatedSubscriptions.some(s => s.enabled && !s.subscribed)
      
      this.setData({
        subscriptions: updatedSubscriptions,
        canSubscribeAny
      })
    }
  },

  onShowGuide() {
    showSubscribeGuide()
  },

  onOpenSettings() {
    wx.openSetting({
      success: (res) => {
        console.log('设置页面返回:', res)
      }
    })
  }
})