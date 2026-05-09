interface Profile {
  userId: number
  userCode: string
  avatarUrl: string
  nickname: string
  gender: 'male' | 'female' | 'unknown' | ''
  birthday: string
  phone: string
  phoneMasked: string
  idCard: string
  idCardMasked: string
  createdAt: number
  updatedAt: number
}

Page({
  data: {
    profile: {
      userId: '',
      avatarUrl: '',
      nickname: '',
      gender: '',
      birthday: '',
      phone: '',
      phoneMasked: '',
      idCard: '',
      idCardMasked: '',
      createdAt: 0,
      updatedAt: 0
    } as Profile,
    originalProfile: {} as Partial<Profile>,
    hasChanged: false,
    isSaved: false,
    age: 0
  },

  onLoad() {
    this.loadProfile()
  },

  onShow() {
    // 页面显示时重新加载数据
    this.loadProfile()
  },

  loadProfile() {
    try {
      // 使用统一的缓存 key: USER_PROFILE
      let stored = wx.getStorageSync('USER_PROFILE')
      
      // 兼容旧数据格式（字符串或对象）
      if (typeof stored === 'string') {
        stored = JSON.parse(stored || '{}')
      }
      
      if (stored && Object.keys(stored).length > 0) {
        const profile = stored
        const birthday = profile.birthday || ''
        console.log('edit 页面读取 USER_PROFILE:', profile)
        this.setData({
          profile: {
            userId: profile.userId || profile.id || 0,
            userCode: profile.userCode || wx.getStorageSync('USER_CODE') || '',
            avatarUrl: profile.avatarUrl || '',
            nickname: profile.nickname || '',
            gender: profile.gender || '',
            birthday: birthday,
            phone: profile.phone || profile.phoneMasked || '',
            phoneMasked: profile.phoneMasked || '',
            idCard: '',  // 不回显完整身份证号
            idCardMasked: profile.idCardMasked || '',
            createdAt: profile.createdAt || Date.now(),
            updatedAt: profile.updatedAt || Date.now()
          },
          originalProfile: { ...profile },
          hasChanged: false,
          age: this.calculateAge(birthday)
        })
      } else {
        // 首次进入，使用默认值
        this.setData({
          profile: {
            userId: 0,
            userCode: '',
            avatarUrl: '',
            nickname: '',
            gender: '',
            birthday: '',
            phone: '',
            phoneMasked: '',
            idCard: '',
            idCardMasked: '',
            createdAt: Date.now(),
            updatedAt: Date.now()
          },
          originalProfile: {},
          hasChanged: false,
          age: 0
        })
      }
    } catch (e) {
      console.error('Load profile failed:', e)
    }
  },

  async onChooseAvatar(e: any) {
    const tempFilePath = e.detail.avatarUrl
    if (!tempFilePath) {
      wx.showToast({
        title: '头像选择失败',
        icon: 'none'
      })
      return
    }

    wx.showLoading({ title: '上传头像中...' })

    try {
      const userId = this.data.profile.userId || wx.getStorageSync('USER_ID')
      const userCode = this.data.profile.userCode || wx.getStorageSync('USER_CODE')

      const uploadRes = await new Promise<any>((resolve, reject) => {
        wx.uploadFile({
          url: 'https://miniprogram.huiliaoyiyuan.com/api/user/avatar/upload',
          filePath: tempFilePath,
          name: 'file',
          formData: {
            userId: String(userId || ''),
            userCode: String(userCode || '')
          },
          success(res) {
            console.log('[edit] upload avatar response:', res)
            resolve(res)
          },
          fail(err) {
            console.error('[edit] upload avatar error:', err)
            reject(err)
          }
        })
      })

      if (uploadRes.statusCode !== 200) {
        throw new Error(`上传失败，状态码: ${uploadRes.statusCode}`)
      }

      const resData = JSON.parse(uploadRes.data)

      if (!resData.success || !resData.data?.avatarUrl) {
        throw new Error(resData.error || '上传返回格式错误')
      }

      const avatarUrl = resData.data.avatarUrl

      console.log('[edit] upload avatar success, url:', avatarUrl)

      this.setData({
        'profile.avatarUrl': avatarUrl,
        hasChanged: true
      })

      wx.hideLoading()
      wx.showToast({
        title: '头像上传成功',
        icon: 'success'
      })

    } catch (error) {
      console.error('[edit] onChooseAvatar error:', error)
      wx.hideLoading()

      this.setData({
        'profile.avatarUrl': tempFilePath,
        hasChanged: true
      })

      wx.showToast({
        title: '头像选择成功，保存时将自动上传',
        icon: 'none'
      })
    }
  },

  onNicknameInput(e: any) {
    const value = e.detail?.value || ''
    console.log('昵称输入:', value)

    this.setData({
      'profile.nickname': value,
      hasChanged: true
    })
  },

  onSelectGender(e: any) {
    const gender = e.currentTarget.dataset.gender
    const currentGender = this.data.profile.gender
    
    // 点击已选中的选项则取消选择
    if (currentGender === gender) {
      this.setData({
        'profile.gender': '',
        hasChanged: true
      })
    } else {
      this.setData({
        'profile.gender': gender,
        hasChanged: true
      })
    }
  },

  onBirthdayChange(e: any) {
    const birthday = e.detail.value
    this.setData({
      'profile.birthday': birthday,
      hasChanged: true,
      age: this.calculateAge(birthday)
    })
  },

  onPhoneInput(e: any) {
    let value = e.detail?.value || ''
    // 只保留数字，最多11位
    value = value.replace(/\D/g, '').slice(0, 11)
    this.setData({
      'profile.phone': value,
      hasChanged: true
    })
  },

  onIdCardInput(e: any) {
    let value = e.detail?.value || ''
    // 只保留数字和X/x，统一转大写，最多18位
    value = value.replace(/[^0-9xX]/g, '').toUpperCase().slice(0, 18)
    this.setData({
      'profile.idCard': value,
      hasChanged: true
    })
  },

  calculateAge(birthday: string): number {
    if (!birthday) return 0
    
    const birthDate = new Date(birthday)
    const now = new Date()
    let age = now.getFullYear() - birthDate.getFullYear()
    
    // 检查是否过了生日
    const monthDiff = now.getMonth() - birthDate.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && now.getDate() < birthDate.getDate())) {
      age--
    }
    
    return Math.max(0, age)
  },

  async onSave() {
    const nickname = (this.data.profile.nickname || '').trim()

    console.log('保存前 profile:', this.data.profile)
    console.log('保存前 nickname:', nickname)

    if (!nickname) {
      wx.showToast({
        title: '请填写昵称',
        icon: 'none'
      })
      return
    }

    const oldStored = wx.getStorageSync('USER_PROFILE')
    let oldProfile: any = {}

    if (oldStored) {
      if (typeof oldStored === 'string') {
        try {
          oldProfile = JSON.parse(oldStored)
        } catch (err) {
          oldProfile = {}
        }
      } else {
        oldProfile = oldStored
      }
    }

    const userId = this.data.profile.userId || oldProfile.userId || oldProfile.id || ''
    if (!userId) {
      wx.showToast({
        title: '用户ID不能为空',
        icon: 'none'
      })
      return
    }

    let avatarUrl = this.data.profile.avatarUrl || oldProfile.avatarUrl || ''

    const isTempPath = avatarUrl && (
      avatarUrl.startsWith('http://tmp/') ||
      avatarUrl.startsWith('wxfile://') ||
      avatarUrl.startsWith('http://')
    )

    const isOfficialUrl = avatarUrl && avatarUrl.startsWith('https://miniprogram.huiliaoyiyuan.com/uploads/avatars/')

    if (isTempPath && !isOfficialUrl) {
      wx.showLoading({ title: '上传头像中...' })

      try {
        const userCode = this.data.profile.userCode || wx.getStorageSync('USER_CODE') || ''

        const uploadRes = await new Promise<any>((resolve, reject) => {
          wx.uploadFile({
            url: 'https://miniprogram.huiliaoyiyuan.com/api/user/avatar/upload',
            filePath: avatarUrl,
            name: 'file',
            formData: {
              userId: String(userId),
              userCode: String(userCode)
            },
            success(res) { resolve(res) },
            fail(err) { reject(err) }
          })
        })

        if (uploadRes.statusCode === 200) {
          const resData = JSON.parse(uploadRes.data)
          if (resData.success && resData.data?.avatarUrl) {
            avatarUrl = resData.data.avatarUrl
            console.log('[edit] save upload avatar success:', avatarUrl)
          }
        }
      } catch (error) {
        console.error('[edit] save upload avatar error:', error)
      }

      wx.hideLoading()
    }

    const profileData = {
      userId: userId,
      nickname: nickname,
      gender: this.data.profile.gender || oldProfile.gender || 'unknown',
      birthday: this.data.profile.birthday || oldProfile.birthday || '',
      avatarUrl: avatarUrl,
      phone: this.data.profile.phone || '',
      idCard: this.data.profile.idCard || ''
    }

    // 敏感信息脱敏打印
    const logData = { ...profileData }
    if (logData.phone && logData.phone.length >= 11) {
      logData.phone = logData.phone.slice(0, 3) + '****' + logData.phone.slice(-4)
    }
    if (logData.idCard && logData.idCard.length >= 18) {
      logData.idCard = logData.idCard.slice(0, 3) + '***********' + logData.idCard.slice(-4)
    }

    wx.showLoading({
      title: '保存中...'
    })

    try {
      const url = 'https://miniprogram.huiliaoyiyuan.com/api/user/profile'
      console.log('保存资料请求URL:', url)
      console.log('保存资料请求参数(脱敏):', JSON.stringify(logData))
      
      // 使用 Promise 包装 wx.request，确保正确获取响应
      const response: any = await new Promise((resolve, reject) => {
        wx.request({
          url: url,
          method: 'POST',
          data: profileData,
          header: { 'Content-Type': 'application/json' },
          success(res) {
            console.log('wx.request success:', res)
            resolve(res)
          },
          fail(err) {
            console.error('wx.request fail:', err)
            reject(err)
          }
        })
      })

      console.log('后端保存返回 statusCode:', response?.statusCode)
      console.log('后端保存返回 data:', JSON.stringify(response?.data))

      // 兼容处理：统一获取响应体
      const raw = response || {}
      const body = raw.data !== undefined ? raw.data : raw
      const payload = body.data !== undefined ? body.data : body
      
      console.log('body:', JSON.stringify(body))
      console.log('payload:', JSON.stringify(payload))

      // 检查是否有错误
      if (body.error) {
        throw new Error(body.error)
      }

      // 检查是否成功（兼容多种返回格式）
      const statusCode = raw.statusCode || (body.statusCode || 200)
      const isSuccess = body.success !== false && statusCode >= 200 && statusCode < 300

      if (isSuccess) {
        // 后端保存成功，合并更新本地缓存
        const oldProfile = wx.getStorageSync('USER_PROFILE') || {}
        
        // 获取脱敏后的敏感信息
        const phone = payload.phone || payload.phoneMasked || ''
        const phoneMasked = payload.phoneMasked || phone
        const idCardMasked = payload.idCardMasked || ''
        
        const updatedProfile = {
          ...oldProfile,
          ...payload,
          userId: oldProfile.userId || wx.getStorageSync('USER_ID') || userId,
          userCode: oldProfile.userCode || wx.getStorageSync('USER_CODE') || '',
          openid: oldProfile.openid || '',
          unionid: oldProfile.unionid || '',
          nickname: this.data.profile.nickname,
          gender: this.data.profile.gender || oldProfile.gender || 'unknown',
          birthday: this.data.profile.birthday,
          avatarUrl: this.data.profile.avatarUrl,
          // 敏感信息（只保存脱敏值）
          phone: phone,
          phoneMasked: phoneMasked,
          idCard: '',  // 不保存完整身份证号到本地
          idCardMasked: idCardMasked,
          updatedAt: Date.now()
        }

        // 更新所有缓存
        wx.setStorageSync('USER_PROFILE', updatedProfile)
        wx.setStorageSync('USER_ID', updatedProfile.userId)
        wx.setStorageSync('USER_CODE', updatedProfile.userCode)
        
        console.log('保存后的 USER_PROFILE:', wx.getStorageSync('USER_PROFILE'))

        this.setData({
          profile: updatedProfile,
          hasChanged: false,
          isSaved: true
        })

        const pages = getCurrentPages()
        const prevPage: any = pages[pages.length - 2]

        if (prevPage && typeof prevPage.loadProfile === 'function') {
          prevPage.loadProfile()
        } else if (prevPage) {
          prevPage.setData({
            profile: updatedProfile
          })
        }

        wx.hideLoading()
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        })

        setTimeout(() => {
          wx.navigateBack()
        }, 600)
      } else {
        throw new Error(body.message || body.errmsg || '保存失败')
      }
    } catch (error) {
      wx.hideLoading()
      console.error('保存失败:', error)
      wx.showToast({
        title: '保存失败，请重试',
        icon: 'none'
      })
    }
  },

  onAvatarError() {
    // 头像加载失败，使用默认头像
    const profile = this.data.profile
    if (profile.avatarUrl) {
      this.setData({
        profile: {
          ...profile,
          avatarUrl: '/assets/icons/mine.png'
        }
      })
    }
  },

  onUnload() {
    if (!this.data.hasChanged || this.data.isSaved) {
      return
    }

    wx.showModal({
      title: '提示',
      content: '资料尚未保存，是否离开？',
      confirmText: '离开',
      cancelText: '继续编辑',
      success: (res) => {
        if (res.confirm) {
          // 用户确认离开，直接返回
        }
      }
    })
  }
})