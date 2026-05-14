import { disableTongueReminder, enableTongueReminder, getTongueReminderStatus, saveTongueReminderConfig } from "../../utils/subscribe"

type ReminderStatus = {
  configured?: boolean
  enabled: boolean
  intervalDays?: number
  remindTime?: string
  frequency?: string
  reminderTime: string
  reminderIntervalDays: number
  templateId?: string
  lastSentDate?: string | null
  nextSendAt?: string | null
  nextRemindAt?: string | null
  lastSentAt?: string | null
}

type FrequencyOption = {
  label: string
  value: number
}

Page({
  data: {
    userId: "",
    isLoading: true,
    isSubmitting: false,
    isSaving: false,
    status: {
      enabled: false,
      reminderTime: "08:00",
      reminderIntervalDays: 1
    } as ReminderStatus,

    // 统一的4个展示字段（必须有默认值）
    frequencyText: "每天提醒",
    reminderTimeText: "08:00",
    sendStatusText: "今日未发送",
    nextReminderText: "等待系统计算",

    // 频率选项
    frequencyOptions: [
      { label: "每天提醒", value: 1 },
      { label: "每2天提醒一次", value: 2 },
      { label: "每3天提醒一次", value: 3 },
      { label: "每7天提醒一次", value: 7 }
    ] as FrequencyOption[],
    selectedFrequencyIndex: 0,

    // 当前选择的配置值（用于提交给后端）
    currentIntervalDays: 1,
    currentReminderTime: "08:00"
  },

  onLoad() {
    const app = getApp<IAppOption>()
    const userId = app.globalData.userId || wx.getStorageSync("USER_ID") || ""
    this.setData({ userId })
    this.loadStatus()
  },

  onShow() {
    if (this.data.userId) {
      this.loadStatus()
    }
  },

  async loadStatus() {
    const userId = this.data.userId
    if (!userId) {
      this.setData({ isLoading: false })
      wx.showToast({
        title: "请先登录",
        icon: "none"
      })
      return
    }

    try {
      const status = await getTongueReminderStatus(userId, "tongue_reminder")

      // 从后端数据中提取实际值
      const intervalDays = Number(status.intervalDays || status.reminderIntervalDays || 1)
      const reminderTime = String(status.remindTime || status.reminderTime || status.time || "08:00")
      const nextSendAt = status.nextRemindAt || status.nextSendAt || status.nextReminderAt || null
      const lastSentAt = status.lastSentAt || null
      const lastSentDate = status.lastSentDate || null

      // 找到频率选项的索引
      const freqIndex = this.data.frequencyOptions.findIndex(
        (opt) => opt.value === intervalDays
      )
      const validIndex = freqIndex >= 0 ? freqIndex : 0

      // 映射为4个统一展示字段
      const frequencyText = this.formatFrequencyText(intervalDays)
      const reminderTimeText = reminderTime
      const sendStatusText = this.formatSendStatusText(lastSentAt, lastSentDate)
      const nextReminderText = this.formatNextReminderText(nextSendAt)

      this.setData({
        status: {
          configured: !!status.configured,
          enabled: !!status.enabled,
          intervalDays,
          remindTime: reminderTime,
          reminderTime: reminderTime,
          reminderIntervalDays: intervalDays,
          templateId: status.templateId,
          lastSentDate: lastSentDate,
          nextSendAt: nextSendAt,
          lastSentAt: lastSentAt
        },
        frequencyText,
        reminderTimeText,
        sendStatusText,
        nextReminderText,
        selectedFrequencyIndex: validIndex,
        currentIntervalDays: intervalDays,
        currentReminderTime: reminderTime,
        isLoading: false
      })
    } catch (error) {
      console.error("[reminder-settings] loadStatus error:", error)
      this.setData({ isLoading: false })
      wx.showToast({
        title: "加载提醒状态失败",
        icon: "none"
      })
    }
  },

  formatFrequencyText(intervalDays: number): string {
    switch (intervalDays) {
      case 1:
        return "每天提醒"
      case 2:
        return "每2天提醒一次"
      case 3:
        return "每3天提醒一次"
      case 7:
        return "每7天提醒一次"
      default:
        return `每${intervalDays}天提醒一次`
    }
  },

  formatSendStatusText(lastSentAt: string | null, lastSentDate: string | null): string {
    if (!lastSentAt && !lastSentDate) {
      return "今日未发送"
    }

    const now = new Date()
    const today = now.toISOString().split("T")[0]

    if (lastSentAt) {
      const sentDate = new Date(lastSentAt).toISOString().split("T")[0]
      if (sentDate === today) {
        return "今日已发送"
      }
    }

    if (lastSentDate) {
      if (lastSentDate === today) {
        return "今日已发送"
      }
    }

    return "今日未发送"
  },

  formatNextReminderText(nextSendAt: string | null): string {
    if (!nextSendAt) {
      return "等待系统计算"
    }

    try {
      const date = new Date(nextSendAt)
      const month = date.getMonth() + 1
      const day = date.getDate()
      const hours = String(date.getHours()).padStart(2, "0")
      const minutes = String(date.getMinutes()).padStart(2, "0")

      return `${month}月${day}日 ${hours}:${minutes}`
    } catch (error) {
      console.error("[reminder-settings] formatNextReminderText error:", error)
      return "等待系统计算"
    }
  },

  onFrequencyChange(e: WechatMiniprogram.PickerSelectorChange) {
    const index = e.detail.value
    const option = this.data.frequencyOptions[index]
    if (option) {
      this.setData({
        selectedFrequencyIndex: index,
        currentIntervalDays: option.value,
        frequencyText: option.label
      })
    }
  },

  onTimeChange(e: WechatMiniprogram.PickerTimeChange) {
    const timeValue = e.detail.value
    this.setData({
      currentReminderTime: timeValue,
      reminderTimeText: timeValue
    })
  },

  async onEnableReminder() {
    if (this.data.isSubmitting) return

    const { userId } = this.data
    if (!userId) {
      wx.showToast({
        title: "请先登录",
        icon: "none"
      })
      return
    }

    if (!this.data.status.configured) {
      wx.showToast({
        title: "请先保存提醒配置",
        icon: "none"
      })
      return
    }

    if (!this.data.status.reminderIntervalDays || !this.data.status.reminderTime) {
      wx.showToast({
        title: "请先保存提醒配置",
        icon: "none"
      })
      return
    }

    this.setData({ isSubmitting: true })
    try {
      const templateId = this.data.status.templateId
      if (!templateId) {
        throw new Error('未找到长期订阅模板ID')
      }

      console.log('准备调用 wx.requestSubscribeMessage')
      const subscribeResult = await new Promise<WechatMiniprogram.SubscribeMessageSuccessCallbackResult>((resolve, reject) => {
        wx.requestSubscribeMessage({
          tmplIds: [templateId],
          success: (res) => {
            resolve(res as WechatMiniprogram.SubscribeMessageSuccessCallbackResult)
          },
          fail: (err) => {
            reject(new Error(err.errMsg || '订阅授权失败'))
          }
        })
      })

      const authStatus = subscribeResult[templateId]
      if (authStatus === 'reject') {
        wx.showToast({
          title: '您已拒绝订阅',
          icon: 'none'
        })
        return
      }

      if (authStatus !== 'accept' && authStatus !== 'ban') {
        throw new Error('订阅授权失败')
      }

      const success = await enableTongueReminder(userId, 'tongue_reminder')

      if (success) {
        wx.showToast({
          title: '已开启提醒',
          icon: 'success'
        })
        await this.loadStatus()
      }
    } catch (error) {
      console.error('[reminder-settings] onEnableReminder error:', error)
      wx.showToast({
        title: error instanceof Error ? error.message : '开启提醒失败',
        icon: 'none'
      })
    } finally {
      this.setData({ isSubmitting: false })
    }
  },

  async onSaveConfig() {
    if (this.data.isSaving) return

    const { userId, currentReminderTime, currentIntervalDays } = this.data
    if (!userId) {
      wx.showToast({
        title: "请先登录",
        icon: "none"
      })
      return
    }

    this.setData({ isSaving: true })
    try {
      await saveTongueReminderConfig(userId, currentReminderTime, currentIntervalDays, 'tongue_reminder')

      wx.showToast({
        title: '保存成功',
        icon: 'success'
      })

      await this.loadStatus()
    } catch (error) {
      console.error('[reminder-settings] save config error:', error)
      wx.showToast({
        title: error instanceof Error ? error.message : '保存配置失败',
        icon: 'none'
      })
    } finally {
      this.setData({ isSaving: false })
    }
  },

  async onDisableReminder() {
    if (this.data.isSubmitting) return

    const { userId } = this.data
    if (!userId) {
      wx.showToast({
        title: "请先登录",
        icon: "none"
      })
      return
    }

    this.setData({ isSubmitting: true })
    try {
      await disableTongueReminder(userId, 'tongue_reminder')
      wx.showToast({
        title: '已关闭提醒',
        icon: 'success'
      })
      await this.loadStatus()
    } catch (error) {
      console.error('[reminder-settings] disable error:', error)
      wx.showToast({
        title: error instanceof Error ? error.message : '关闭提醒失败',
        icon: 'none'
      })
    } finally {
      this.setData({ isSubmitting: false })
    }
  },

  onGoTongueUpload() {
    wx.navigateTo({
      url: "/pages/tongue-upload/tongue-upload"
    })
  }
})
