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

function requestWxLogin(code: string, retryCount: number = 0): Promise<WechatLoginResponse> {
  return new Promise((resolve, reject) => {
    const maxRetries = 3
    const loginUrl = 'https://miniprogram.huiliaoyiyuan.com/api/wxapp/login'
    
    console.log(`[app] Login attempt ${retryCount + 1}/${maxRetries + 1}, URL: ${loginUrl}`)
    
    wx.request({
      url: loginUrl,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: { code },
      timeout: 10000,
      success(res) {
        console.log(`[app] Login response: statusCode=${res.statusCode}`)
        
        if (res.statusCode >= 200 && res.statusCode < 300) {
          console.log('[app] Login successful')
          resolve(res.data as WechatLoginResponse)
        } else if (res.statusCode === 502 || res.statusCode === 503) {
          // Server error, retry
          if (retryCount < maxRetries) {
            console.warn(`[app] Server error (${res.statusCode}), retrying... (${retryCount + 1}/${maxRetries})`)
            setTimeout(() => {
              requestWxLogin(code, retryCount + 1).then(resolve).catch(reject)
            }, 2000 * (retryCount + 1)) // Exponential backoff
          } else {
            console.error(`[app] Login failed after ${maxRetries} retries with status ${res.statusCode}`)
            reject({
              statusCode: res.statusCode,
              data: res.data,
              message: '服务器暂时不可用，请稍后重试'
            })
          }
        } else {
          console.error(`[app] Login failed with status ${res.statusCode}:`, res.data)
          reject({
            statusCode: res.statusCode,
            data: res.data
          })
        }
      },
      fail(err) {
        console.error('[app] Login request failed:', err)
        if (retryCount < maxRetries) {
          console.warn(`[app] Network error, retrying... (${retryCount + 1}/${maxRetries})`)
          setTimeout(() => {
            requestWxLogin(code, retryCount + 1).then(resolve).catch(reject)
          }, 2000 * (retryCount + 1))
        } else {
          reject(err)
        }
      }
    })
  })
}

function readCachedProfile(): Record<string, any> {
  const cachedProfile = wx.getStorageSync('USER_PROFILE')

  if (!cachedProfile) {
    return {}
  }

  if (typeof cachedProfile === 'string') {
    try {
      const parsed = JSON.parse(cachedProfile)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch (error) {
      return {}
    }
  }

  if (typeof cachedProfile === 'object') {
    return cachedProfile
  }

  return {}
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
    const cachedProfile = readCachedProfile()
    if (cachedProfile && cachedProfile.userId) {
      this.globalData.userId = cachedProfile.userId
      this.globalData.userCode = cachedProfile.userCode || ''
      this.globalData.userProfile = cachedProfile
      this.globalData.loginReady = true
    }
  },

  startLogin() {
    if (this.globalData.isLoggingIn) {
      console.log('[app] Already logging in, skipping...')
      return
    }
    if (this.globalData.loginPromise) {
      console.log('[app] Login promise already exists, skipping...')
      return
    }

    this.globalData.isLoggingIn = true
    console.log('[app] Starting login process...')

    this.globalData.loginPromise = new Promise<void>((resolve) => {
      wx.login({
        success: async (res) => {
          if (res.code) {
            try {
              console.log('[app] Got WeChat login code, requesting backend login...')
              const loginData = await requestWxLogin(res.code)

              if (loginData && loginData.userId) {
                const cachedProfile = readCachedProfile()
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
                const mergedProfile = {
                  ...cachedProfile,
                  ...currentUser
                }

                wx.setStorageSync('USER_ID', currentUser.userId)
                wx.setStorageSync('USER_CODE', currentUser.userCode)
                wx.setStorageSync('USER_PROFILE', mergedProfile)

                this.globalData.userId = mergedProfile.userId
                this.globalData.userCode = mergedProfile.userCode
                this.globalData.userProfile = mergedProfile
                this.globalData.loginReady = true

                console.log('[app] 登录成功, userId:', currentUser.userId, ', userCode:', currentUser.userCode)

                // 通知所有等待的回调
                this.notifyLoginComplete(mergedProfile)
              } else {
                console.warn('[app] Login response missing userId or userCode')
              }
            } catch (error: any) {
              console.error('[app] 登录请求异常:', error?.message || error)
              // Mark as ready even if login fails, so the app can continue with offline mode
              this.globalData.loginReady = true
              this.notifyLoginComplete(null)
            }
          } else {
            console.error('[app] Failed to get WeChat login code')
            this.globalData.loginReady = true
            this.notifyLoginComplete(null)
          }

          this.globalData.isLoggingIn = false
          resolve()
        },
        fail: (err) => {
          console.error('[app] wx.login failed:', err)
          this.globalData.isLoggingIn = false
          this.globalData.loginReady = true
          this.notifyLoginComplete(null)
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
