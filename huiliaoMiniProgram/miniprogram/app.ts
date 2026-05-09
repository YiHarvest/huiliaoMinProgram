// app.ts

interface WechatLoginResponse {
  userId: number
  userCode: string
  openid: string
  unionid?: string
  profile?: {
    nickname?: string
    avatarUrl?: string
    gender?: string
    birthday?: string
    age?: string
    updatedAt?: string
  }
  hasProfile?: boolean
}

function requestWxLogin(code: string): Promise<WechatLoginResponse> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: 'https://miniprogram.huiliaoyiyuan.com/api/wxapp/login',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: { code },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as WechatLoginResponse)
        } else {
          reject({
            statusCode: res.statusCode,
            data: res.data
          })
        }
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

App<IAppOption>({
  globalData: {
    loginPromise: null as any,
    isLoggingIn: false,
    loginReady: false,
    loginCallbacks: [] as Array<(user: any) => void>,
    userId: 0,
    userCode: '',
    userProfile: null as any
  },

  onLaunch() {
    const logs = wx.getStorageSync('logs') || []
    logs.unshift(Date.now())
    wx.setStorageSync('logs', logs)

    this.restoreFromCache()
    this.startLogin()
  },

  restoreFromCache() {
    const cachedProfile = wx.getStorageSync('USER_PROFILE')
    if (cachedProfile && cachedProfile.userId) {
      this.globalData.userId = cachedProfile.userId
      this.globalData.userCode = cachedProfile.userCode || ''
      this.globalData.userProfile = cachedProfile
      this.globalData.loginReady = true
    }
  },

  startLogin() {
    if (this.globalData.isLoggingIn) return
    if (this.globalData.loginPromise) return

    this.globalData.isLoggingIn = true

    this.globalData.loginPromise = new Promise<void>((resolve) => {
      wx.login({
        success: async (res) => {
          if (res.code) {
            try {
              const loginData = await requestWxLogin(res.code)

              if (loginData && loginData.userId) {
                const currentUser = {
                  userId: loginData.userId,
                  userCode: loginData.userCode,
                  openid: loginData.openid || '',
                  unionid: loginData.unionid || '',
                  nickname: loginData.profile?.nickname || '',
                  avatarUrl: loginData.profile?.avatarUrl || '/assets/icons/mine.png',
                  gender: loginData.profile?.gender || '',
                  birthday: loginData.profile?.birthday || '',
                  hasProfile: loginData.hasProfile === true || !!loginData.profile
                }

                wx.setStorageSync('USER_ID', currentUser.userId)
                wx.setStorageSync('USER_CODE', currentUser.userCode)
                wx.setStorageSync('USER_PROFILE', currentUser)

                this.globalData.userId = currentUser.userId
                this.globalData.userCode = currentUser.userCode
                this.globalData.userProfile = currentUser
                this.globalData.loginReady = true

                console.log('[app] 登录成功, userCode:', currentUser.userCode)

                // 通知所有等待的回调
                this.notifyLoginComplete(currentUser)
              }
            } catch (error) {
              console.error('[app] 登录请求异常:', error)
            }
          }

          this.globalData.isLoggingIn = false
          resolve()
        },
        fail: () => {
          this.globalData.isLoggingIn = false
          resolve()
        }
      })
    })
  },

  notifyLoginComplete(user: any) {
    if (this.globalData.loginCallbacks.length > 0) {
      console.log('[app] 触发', this.globalData.loginCallbacks.length, '个登录回调')
      const callbacks = [...this.globalData.loginCallbacks]
      this.globalData.loginCallbacks = []
      callbacks.forEach(cb => {
        try {
          cb(user)
        } catch (e) {
          console.error('[app] 回调执行失败:', e)
        }
      })
    }
  },

  registerLoginCallback(callback: (user: any) => void) {
    if (this.globalData.loginReady && this.globalData.userProfile) {
      callback(this.globalData.userProfile)
    } else {
      this.globalData.loginCallbacks.push(callback)
    }
  },

  ensureLogin(): Promise<void> {
    if (this.globalData.loginPromise) {
      return this.globalData.loginPromise
    }
    return new Promise(resolve => resolve())
  }
})
