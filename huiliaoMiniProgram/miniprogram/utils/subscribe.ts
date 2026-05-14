const SUBSCRIBE_API_BASE_URL = "https://miniprogram.huiliaoyiyuan.com"

type SubscribeScene = "ai_reply" | "tongue_result" | "appointment_reminder" | "tongue_reminder"

type SubscribeConfig = {
  scene: SubscribeScene
  name: string
  description: string
  templateId: string
  page: string
  enabled: boolean
}

type SubscribeRequestPayload = {
  openid: string
  templateId: string
  scene: SubscribeScene
  subscribeStatus: "accept" | "reject"
}

type SubscribeResponse = {
  success: boolean
  message?: string
}

type TongueReminderStatus = {
  scene?: string
  configured?: boolean
  userId?: number | string
  openid?: string
  templateId?: string
  enabled: boolean
  frequency?: string
  reminderTime?: string
  remindTime?: string
  reminderIntervalDays?: number
  lastSentDate?: string | null
  nextSendAt?: string | null
  nextRemindAt?: string | null
  lastSentAt?: string | null
}

export function requestSubscribeMessage(
  tmplIds: string[],
  _scene: SubscribeScene
): Promise<Record<string, "accept" | "reject" | "ban">> {
  return new Promise((resolve, reject) => {
    wx.requestSubscribeMessage({
      tmplIds,
      success: (res) => resolve(res),
      fail: (error) => reject(new Error(error.errMsg || "订阅请求失败"))
    })
  })
}

export async function saveSubscriptionRecord(
  payload: SubscribeRequestPayload
): Promise<SubscribeResponse> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${SUBSCRIBE_API_BASE_URL}/api/subscription/record`,
      method: "POST",
      data: payload,
      header: {
        "content-type": "application/json"
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error("保存订阅记录失败"))
          return
        }

        resolve((res.data || {}) as SubscribeResponse)
      },
      fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
    })
  })
}

export async function getSubscribeConfig(): Promise<{
  configured: boolean
  scenes: SubscribeConfig[]
}> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${SUBSCRIBE_API_BASE_URL}/api/subscription/config`,
      method: "GET",
      header: {
        "content-type": "application/json"
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error("获取订阅配置失败"))
          return
        }

        resolve(res.data as { configured: boolean; scenes: SubscribeConfig[] })
      },
      fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
    })
  })
}

export async function getTongueReminderStatus(
  userId: string | number,
  scene: SubscribeScene = "tongue_reminder"
): Promise<TongueReminderStatus> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${SUBSCRIBE_API_BASE_URL}/api/subscription/status`,
      method: "GET",
      data: { userId, scene },
      header: {
        "content-type": "application/json"
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error((res.data as any)?.error || "获取舌苔提醒状态失败"))
          return
        }

        const responseData = res.data as any
        resolve((responseData?.data || responseData) as TongueReminderStatus)
      },
      fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
    })
  })
}

export async function enableTongueReminder(
  userId: string | number,
  scene: SubscribeScene = "tongue_reminder"
): Promise<boolean> {
  try {
    await new Promise((resolve, reject) => {
      wx.request({
        url: `${SUBSCRIBE_API_BASE_URL}/api/subscription/enable`,
        method: "POST",
        data: {
          userId,
          scene
        },
        header: {
          "content-type": "application/json"
        },
        success: (res) => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error((res.data as any)?.error || "开启提醒失败"))
            return
          }
          resolve((res.data as any)?.data || res.data)
        },
        fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
      })
    })

    wx.showToast({
      title: "已开启提醒",
      icon: "success"
    })
    return true
  } catch (error) {
    console.error("开启舌苔提醒失败", error)
    wx.showToast({
      title: error instanceof Error ? error.message : "舌苔提醒设置失败",
      icon: "none"
    })
    return false
  }
}

export async function disableTongueReminder(
  userId: string | number,
  scene: SubscribeScene = "tongue_reminder"
): Promise<boolean> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${SUBSCRIBE_API_BASE_URL}/api/subscription/disable`,
      method: "POST",
      data: { userId, scene },
      header: {
        "content-type": "application/json"
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error((res.data as any)?.error || "关闭提醒失败"))
          return
        }
        resolve(true)
      },
      fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
    })
  })
}

export async function saveTongueReminderConfig(
  userId: string | number,
  reminderTime: string,
  reminderIntervalDays: number,
  scene: SubscribeScene = "tongue_reminder"
): Promise<boolean> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${SUBSCRIBE_API_BASE_URL}/api/subscription/config`,
      method: "POST",
      data: {
        userId,
        scene,
        intervalDays: reminderIntervalDays,
        remindTime: reminderTime
      },
      header: {
        "content-type": "application/json"
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error((res.data as any)?.error || "保存提醒配置失败"))
          return
        }
        resolve(true)
      },
      fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
    })
  })
}

export async function handleSubscribeAuthorization(
  openid: string,
  scenes: SubscribeScene[]
): Promise<{ success: boolean; subscribedScenes: SubscribeScene[] }> {
  try {
    const config = await getSubscribeConfig()

    if (!config.configured) {
      wx.showModal({
        title: "提示",
        content: "订阅消息功能尚未配置，请联系管理员。",
        showCancel: false
      })
      return { success: false, subscribedScenes: [] }
    }

    const enabledScenes = config.scenes.filter((s) => s.enabled && scenes.includes(s.scene))

    if (enabledScenes.length === 0) {
      wx.showToast({
        title: "没有可订阅的消息类型",
        icon: "none"
      })
      return { success: false, subscribedScenes: [] }
    }

    const tmplIds = enabledScenes.map((s) => s.templateId)
    const subscribeResult = await requestSubscribeMessage(tmplIds, scenes[0])

    const subscribedScenes: SubscribeScene[] = []
    const rejectedScenes: SubscribeScene[] = []

    for (const scene of enabledScenes) {
      const result = subscribeResult[scene.templateId]

      if (result === "accept") {
        try {
          await saveSubscriptionRecord({
            openid,
            templateId: scene.templateId,
            scene: scene.scene,
            subscribeStatus: "accept"
          })
          subscribedScenes.push(scene.scene)
        } catch (error) {
          console.error("保存订阅记录失败:", error)
        }
      } else if (result === "reject" || result === "ban") {
        rejectedScenes.push(scene.scene)
      }
    }

    if (subscribedScenes.length > 0) {
      wx.showToast({
        title: `成功订阅 ${subscribedScenes.length} 种消息`,
        icon: "success"
      })
    } else if (rejectedScenes.length > 0) {
      wx.showModal({
        title: "订阅提醒",
        content: "您已拒绝订阅消息。如需开启，请前往小程序设置页面手动开启。",
        confirmText: "去设置",
        success: (res) => {
          if (res.confirm) {
            wx.openSetting()
          }
        }
      })
    }

    return { success: subscribedScenes.length > 0, subscribedScenes }
  } catch (error) {
    console.error("订阅授权失败:", error)
    wx.showToast({
      title: error instanceof Error ? error.message : "订阅失败，请稍后重试",
      icon: "none"
    })
    return { success: false, subscribedScenes: [] }
  }
}

export function showSubscribeGuide() {
  wx.showModal({
    title: "消息订阅说明",
    content: "开启消息订阅后，您将收到以下提醒：\n\n1. AI问答回复完成\n2. 舌诊报告生成完成\n3. 预约/复诊提醒\n4. 每日舌苔拍摄提醒\n\n您可以在设置页面管理订阅状态。",
    confirmText: "知道了",
    showCancel: false
  })
}
