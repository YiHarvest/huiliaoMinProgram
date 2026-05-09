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
      id_card_masked: ''
    },
    profileProgress: {
      percent: 0,
      completed: 0,
      total: 8,
      text: '已完善基础资料'
    }
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
      ...cachedProfile,
      ...globalProfile,
      userId: userId,
      userCode: userCode,
      nickname: globalProfile.nickname || cachedProfile.nickname || '用户昵称',
      avatarUrl: globalProfile.avatarUrl || cachedProfile.avatarUrl || '/assets/icons/mine.png',
      gender: globalProfile.gender || cachedProfile.gender || '',
      birthday: globalProfile.birthday || cachedProfile.birthday || '',
      age: globalProfile.age || cachedProfile.age || '',
      phone: globalProfile.phone || cachedProfile.phone || '',
      phoneMasked: globalProfile.phoneMasked || cachedProfile.phoneMasked || '',
      phone_masked: globalProfile.phone_masked || cachedProfile.phone_masked || '',
      idCard: globalProfile.idCard || cachedProfile.idCard || '',
      idCardMasked: globalProfile.idCardMasked || cachedProfile.idCardMasked || '',
      id_card_masked: globalProfile.id_card_masked || cachedProfile.id_card_masked || ''
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
      const response = await wx.request({
        url: 'https://miniprogram.huiliaoyiyuan.com/api/user/profile',
        method: 'GET',
        data: { userId },
        header: { 'Content-Type': 'application/json' }
      })

      if (response.statusCode === 200 && response.data?.data) {
        const backendData = response.data.data
        const oldProfile = wx.getStorageSync('USER_PROFILE') || {}

        const currentAvatarUrl = this.data.profile.avatarUrl || ''
        const isOfficialAvatar = currentAvatarUrl.startsWith('https://miniprogram.huiliaoyiyuan.com/uploads/avatars/')

        let finalAvatarUrl = backendData.avatarUrl || ''

        if (!finalAvatarUrl && isOfficialAvatar) {
          finalAvatarUrl = currentAvatarUrl
        } else if (!finalAvatarUrl && oldProfile.avatarUrl) {
          finalAvatarUrl = oldProfile.avatarUrl
        }

        const mergedProfile = {
          ...oldProfile,
          ...backendData,
          userId: oldProfile.userId || userId,
          userCode: oldProfile.userCode || wx.getStorageSync('USER_CODE') || this.data.profile.userCode,
          avatarUrl: finalAvatarUrl
        }

        wx.setStorageSync('USER_PROFILE', mergedProfile)

        const app = getApp()
        if (app?.globalData) {
          app.globalData.userProfile = mergedProfile
        }

        const profileData = {
            userId: mergedProfile.userId,
            userCode: mergedProfile.userCode,
            nickname: mergedProfile.nickname || '用户昵称',
            avatarUrl: finalAvatarUrl || '/assets/icons/mine.png',
            gender: mergedProfile.gender || '',
            birthday: mergedProfile.birthday || '',
            age: mergedProfile.age || '',
            phone: mergedProfile.phone || '',
            phoneMasked: mergedProfile.phoneMasked || '',
            phone_masked: mergedProfile.phone_masked || '',
            idCard: mergedProfile.idCard || '',
            idCardMasked: mergedProfile.idCardMasked || '',
            id_card_masked: mergedProfile.id_card_masked || ''
          }

          const progress = this.computeProfileProgress(profileData)

          this.setData({
            profile: profileData,
            profileProgress: progress
          })
      }
    } catch (error) {
      console.error('[mine] fetchFromBackend error:', error)
    }
  },

  computeProfileProgress(profile: any) {
    let completed = 0
    const total = 8

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

    const avatarDone = isValidValue(profile.avatarUrl) && profile.avatarUrl !== '/assets/icons/mine.png'
    const nicknameDone = isValidValue(profile.nickname) && profile.nickname !== '用户昵称'
    const userCodeDone = isValidValue(profile.userCode) || isValidValue(profile.userId)
    const genderDone = isValidValue(profile.gender) && profile.gender !== 'unknown' && profile.gender !== '不愿透露'
    const birthdayDone = isValidValue(profile.birthday)
    const phoneDone = isValidValue(profile.phone) || isValidValue(profile.phoneMasked) || isValidValue(profile.phone_masked)
    const idCardDone = isValidValue(profile.idCard) || isValidValue(profile.idCardMasked) || isValidValue(profile.id_card_masked)
    const ageFromBirthdayDone = birthdayDone

    if (avatarDone) completed++
    if (nicknameDone) completed++
    if (userCodeDone) completed++
    if (genderDone) completed++
    if (birthdayDone) completed++
    if (phoneDone) completed++
    if (idCardDone) completed++
    if (ageFromBirthdayDone) completed++

    console.log('[mine] profile progress debug:', {
      avatar: avatarDone,
      nickname: nicknameDone,
      userCode: userCodeDone,
      gender: genderDone,
      birthday: birthdayDone,
      phone: phoneDone,
      idCard: idCardDone,
      ageFromBirthday: ageFromBirthdayDone,
      completed: completed,
      total: total,
      profile: profile
    })

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
      url: '/pages/profile/edit'
    })
  },

  onNavigateToPersonalData() {
    wx.navigateTo({
      url: '/pages/personal-data/index'
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
