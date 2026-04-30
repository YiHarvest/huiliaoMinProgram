interface Profile {
  userId: string
  avatarUrl: string
  nickname: string
  gender: 'male' | 'female' | 'unknown' | ''
  birthday: string
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
            userId: profile.userId || 'test_user_id',
            avatarUrl: profile.avatarUrl || '',
            nickname: profile.nickname || '',
            gender: profile.gender || '',
            birthday: birthday,
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
            userId: 'test_user_id',
            avatarUrl: '',
            nickname: '',
            gender: '',
            birthday: '',
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

  onChooseAvatar(e: any) {
    const avatarUrl = e.detail.avatarUrl
    if (!avatarUrl) {
      wx.showToast({
        title: '头像选择失败',
        icon: 'none'
      })
      return
    }
    this.setData({
      'profile.avatarUrl': avatarUrl,
      hasChanged: true
    })
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

  onSave() {
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

    const profile = {
      ...oldProfile,
      ...this.data.profile,
      userId: this.data.profile.userId || oldProfile.userId || 'test_user_id',
      avatarUrl: this.data.profile.avatarUrl || oldProfile.avatarUrl || '',
      nickname,
      gender: this.data.profile.gender || oldProfile.gender || 'unknown',
      birthday: this.data.profile.birthday || oldProfile.birthday || '',
      age: this.data.profile.age || oldProfile.age || 0,
      updatedAt: Date.now()
    }

    wx.setStorageSync('USER_PROFILE', profile)

    console.log('保存后的 USER_PROFILE:', wx.getStorageSync('USER_PROFILE'))

    this.setData({
      profile,
      hasChanged: false,
      isSaved: true
    })

    const pages = getCurrentPages()
    const prevPage: any = pages[pages.length - 2]

    if (prevPage && typeof prevPage.loadProfile === 'function') {
      prevPage.loadProfile()
    } else if (prevPage) {
      prevPage.setData({
        profile
      })
    }

    wx.showToast({
      title: '保存成功',
      icon: 'success'
    })

    setTimeout(() => {
      wx.navigateBack()
    }, 600)
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