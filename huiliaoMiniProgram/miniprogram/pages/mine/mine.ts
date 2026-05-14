Page({
  data: {
    profile: {
      userId: '',
      userCode: '',
      avatarUrl: '/assets/icons/mine.png',
      nickname: '用户昵称',
      gender: '',
      birthday: '',
      age: '',
      phone: '',
      phoneMasked: '',
      phone_masked: '',
      idCard: '',
      idCardMasked: '',
      id_card_masked: '',
      hasPhone: false,
      hasIdCard: false
    },
    profileProgress: {
      percent: 0,
      completed: 0,
      total: 8,
      text: '已完善基础资料'
    }
  },

  extractProfileFromResponse(res: any) {
    if (res?.success === true && res?.data) {
      return res.data
    }

    if (res?.data?.success === true && res?.data?.data) {
      return res.data.data
    }

    if (res?.nickname || res?.avatarUrl || res?.hasPhone !== undefined || res?.hasIdCard !== undefined) {
      return res
    }

    return {}
  },

  onShow() {
    console.log('[mine] onShow called')
    this.loadUserProfile()
  },

  loadUserProfile() {
    console.log('[mine] loadUserProfile called')
    
    const app = getApp()
    
    const globalProfile = (app && app.globalData && app.globalData.userProfile) || {}
    let cachedProfile = wx.getStorageSync('USER_PROFILE')

    if (typeof cachedProfile === 'string') {
      try {
        cachedProfile = JSON.parse(cachedProfile)
      } catch (e) {
        cachedProfile = {}
      }
    }

    if (!cachedProfile || typeof cachedProfile !== 'object') {
      cachedProfile = {}
    }

    const userId = globalProfile.userId || cachedProfile.userId || wx.getStorageSync('USER_ID') || ''
    const userCode = globalProfile.userCode || cachedProfile.userCode || wx.getStorageSync('USER_CODE') || ''

    console.log('[mine] storage USER_CODE:', wx.getStorageSync('USER_CODE'))
    console.log('[mine] globalData userCode:', globalProfile.userCode)
    console.log('[mine] cached userCode:', cachedProfile.userCode)
    console.log('[mine] final userCode:', userCode)

    const profile = {
      ...globalProfile,
      ...cachedProfile,
      userId: userId,
      userCode: userCode,
      nickname: cachedProfile.nickname || globalProfile.nickname || '用户昵称',
      avatarUrl: cachedProfile.avatarUrl || globalProfile.avatarUrl || '/assets/icons/mine.png',
      gender: cachedProfile.gender || globalProfile.gender || '',
      birthday: cachedProfile.birthday || globalProfile.birthday || '',
      age: cachedProfile.age || globalProfile.age || '',
      phone: cachedProfile.phone || globalProfile.phone || '',
      phoneMasked: cachedProfile.phoneMasked || globalProfile.phoneMasked || '',
      phone_masked: cachedProfile.phone_masked || globalProfile.phone_masked || '',
      idCard: cachedProfile.idCard || globalProfile.idCard || '',
      idCardMasked: cachedProfile.idCardMasked || globalProfile.idCardMasked || '',
      id_card_masked: cachedProfile.id_card_masked || globalProfile.id_card_masked || '',
      hasPhone: (cachedProfile.hasPhone === true || globalProfile.hasPhone === true) ? true : false,
      hasIdCard: (cachedProfile.hasIdCard === true || globalProfile.hasIdCard === true) ? true : false
    }

    console.log('[mine] final profile.userCode:', profile.userCode)

    const progress = this.computeProfileProgress(profile)

    this.setData({
      profile: profile,
      profileProgress: progress
    })

    if (userId) {
      this.fetchFromBackend()
    }
  },

  async fetchFromBackend() {
    const userId = this.data.profile.userId || wx.getStorageSync('USER_ID')
    if (!userId) return

    try {
      const apiBody = await new Promise((resolve, reject) => {
        wx.request({
          url: `https://miniprogram.huiliaoyiyuan.com/api/user/profile?userId=${userId}`,
          method: 'GET',
          header: { 'Content-Type': 'application/json' },
          success: (res) => resolve(res.data),
          fail: (err) => reject(err)
        })
      })

      console.log('[mine/profile api body]', apiBody)
      console.log('[mine/profile api body].success', apiBody?.success)
      console.log('[mine/profile api body].data', apiBody?.data)

      if (!apiBody || !apiBody.success || !apiBody.data) {
        console.warn('[mine/api] 接口返回异常或无数据', apiBody)
        return
      }

      const serverProfile = apiBody.data

      console.log('[mine/serverProfile extracted]', serverProfile)
      console.log('[mine/serverProfile] hasPhone =', serverProfile.hasPhone, 'type:', typeof serverProfile.hasPhone)
      console.log('[mine/serverProfile] hasIdCard =', serverProfile.hasIdCard, 'type:', typeof serverProfile.hasIdCard)

      const localProfile = wx.getStorageSync('USER_PROFILE') || {}
      const currentAvatarUrl = this.data.profile.avatarUrl || ''
      const isOfficialAvatar = currentAvatarUrl.startsWith('https://miniprogram.huiliaoyiyuan.com/uploads/avatars/')

      let finalAvatarUrl = serverProfile.avatarUrl || ''

      if (!finalAvatarUrl && isOfficialAvatar) {
        finalAvatarUrl = currentAvatarUrl
      } else if (!finalAvatarUrl && localProfile.avatarUrl) {
        finalAvatarUrl = localProfile.avatarUrl
      }

      const defaultProfile = {
        nickname: '用户昵称',
        avatarUrl: '/assets/icons/mine.png',
        gender: '',
        birthday: '',
        age: '',
        phone: '',
        phoneMasked: '',
        phone_masked: '',
        idCard: '',
        idCardMasked: '',
        id_card_masked: ''
      }

      const finalProfile = {
        ...defaultProfile,
        ...localProfile,
        ...serverProfile,
        userId: localProfile.userId || userId,
        userCode: localProfile.userCode || wx.getStorageSync('USER_CODE') || serverProfile.userCode || this.data.profile.userCode,
        avatarUrl: finalAvatarUrl,

        phoneMasked: serverProfile.phoneMasked || serverProfile.phone_masked || localProfile.phoneMasked || '',
        idCardMasked: serverProfile.idCardMasked || serverProfile.id_card_masked || localProfile.idCardMasked || '',

        hasPhone: serverProfile.hasPhone === true,
        hasIdCard: serverProfile.hasIdCard === true
      }

      console.log('[mine/finalProfile before progress]', finalProfile)
      console.log('[mine/finalProfile] 关键字段验证:', {
        hasPhone: finalProfile.hasPhone,
        hasIdCard: finalProfile.hasIdCard,
        phoneMasked: finalProfile.phoneMasked,
        idCardMasked: finalProfile.idCardMasked
      })

      wx.setStorageSync('USER_PROFILE', finalProfile)

      const app = getApp()
      if (app?.globalData) {
        app.globalData.userProfile = finalProfile
      }

      const progress = this.computeProfileProgress(finalProfile)

      this.setData({
        profile: finalProfile,
        profileProgress: progress
      })
    } catch (error) {
      console.error('[mine] fetchFromBackend error:', error)
    }
  },

  computeProfileProgress(profile: any) {
    let completed = 0
    const total = 8

    console.log('[mine/profile raw]', JSON.stringify(profile, null, 2))

    const isValidValue = (val: any) => {
      if (val === null || val === undefined) return false
      if (typeof val === 'string') {
        const trimmed = val.trim()
        return trimmed !== '' &&
               trimmed !== '请输入手机号' &&
               trimmed !== '请输入身份证号' &&
               trimmed !== '请输入'
      }
      return true
    }

    const normalizedProfile = {
      avatarUrl: profile.avatarUrl,
      nickname: profile.nickname,
      userCode: profile.userCode,
      userId: profile.userId,
      gender: profile.gender,
      birthday: profile.birthday,
      phone: profile.phone,
      phoneMasked: profile.phoneMasked,
      hasPhone: profile.hasPhone,
      idCard: profile.idCard,
      idCardMasked: profile.idCardMasked,
      hasIdCard: profile.hasIdCard
    }

    console.log('[mine/profile normalized]', normalizedProfile)

    const checks = [
      {
        field: 'avatarUrl',
        value: profile.avatarUrl,
        ok: isValidValue(profile.avatarUrl) && profile.avatarUrl !== '/assets/icons/mine.png',
        rule: '非空且非默认头像'
      },
      {
        field: 'nickname',
        value: profile.nickname,
        ok: isValidValue(profile.nickname) && profile.nickname !== '用户昵称',
        rule: '非空且非默认昵称'
      },
      {
        field: 'userCode/userId',
        value: `${profile.userCode || ''}/${profile.userId || ''}`,
        ok: isValidValue(profile.userCode) || isValidValue(profile.userId),
        rule: 'userCode或userId任一有效'
      },
      {
        field: 'gender',
        value: profile.gender,
        ok: isValidValue(profile.gender) && profile.gender !== 'unknown' && profile.gender !== '不愿透露',
        rule: '非空且非unknown/不愿透露'
      },
      {
        field: 'birthday',
        value: profile.birthday,
        ok: isValidValue(profile.birthday),
        rule: '非空即可'
      },
      {
        field: 'phone',
        value: `hasPhone=${profile.hasPhone}`,
        ok: profile.hasPhone === true,
        rule: 'hasPhone为true'
      },
      {
        field: 'idCard',
        value: `hasIdCard=${profile.hasIdCard}`,
        ok: profile.hasIdCard === true,
        rule: 'hasIdCard为true'
      },
      {
        field: 'age',
        value: profile.birthday ? '从birthday推导' : '-',
        ok: isValidValue(profile.birthday),
        rule: '依赖birthday字段'
      }
    ]

    checks.forEach(check => {
      if (check.ok) completed++
    })

    console.table(checks)

    console.log(`[mine/profile progress] 完成 ${completed}/${total} = ${Math.round((completed / total) * 100)}%`)

    const percent = Math.round((completed / total) * 100)
    const text = percent === 100 ? '已完善基础资料' : `已完善 ${percent}%`

    return {
      percent: percent,
      completed: completed,
      total: total,
      text: text
    }
  },

  calculateAge(birthday: string): number {
    if (!birthday) return 0

    const birthDate = new Date(birthday)
    const now = new Date()
    let age = now.getFullYear() - birthDate.getFullYear()
    const monthDiff = now.getMonth() - birthDate.getMonth()

    if (monthDiff < 0 || (monthDiff === 0 && now.getDate() < birthDate.getDate())) {
      age--
    }

    return Math.max(0, age)
  },

  onEditProfile() {
    wx.navigateTo({
      url: '/pages/profile/edit',
      events: {
        profileUpdated: (data: any) => {
          console.log('[mine] 收到 profileUpdated 事件:', data)
          if (data && typeof data === 'object') {
            this.updateProfileFromEdit(data)
          }
        }
      }
    })
  },

  updateProfileFromEdit(profileData: any) {
    console.log('[mine] updateProfileFromEdit 被调用，立即更新界面')
    
    const currentProfile = { ...this.data.profile }
    const updatedProfile = {
      ...currentProfile,
      ...profileData,
      nickname: profileData.nickname || currentProfile.nickname,
      avatarUrl: profileData.avatarUrl || currentProfile.avatarUrl,
      gender: profileData.gender || currentProfile.gender,
      birthday: profileData.birthday || currentProfile.birthday
    }

    const progress = this.computeProfileProgress(updatedProfile)

    this.setData({
      profile: updatedProfile,
      profileProgress: progress
    })

    console.log('[mine] 界面已更新 - nickname:', updatedProfile.nickname, 'avatarUrl:', updatedProfile.avatarUrl)
  },

  onNavigateToPersonalData() {
    wx.navigateTo({
      url: '/pages/personal-data/index'
    })
  },

  onReminderSettings() {
    wx.navigateTo({
      url: '/pages/reminder-settings/reminder-settings'
    })
  },

  onContactUs() {
    wx.navigateTo({
      url: '/pages/contact/contact'
    })
  },

  onFAQ() {
    wx.navigateTo({
      url: '/pages/faq/faq'
    })
  },

  onPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    })
  },

  onUserAgreement() {
    wx.navigateTo({
      url: '/pages/agreement/agreement'
    })
  },

  onAvatarError() {
    const profile = this.data.profile
    if (profile.avatarUrl && profile.avatarUrl !== '/assets/icons/mine.png') {
      this.setData({
        'profile.avatarUrl': '/assets/icons/mine.png'
      })
    }
  }
})
