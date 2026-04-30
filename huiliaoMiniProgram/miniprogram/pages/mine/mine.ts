Component({
  data: {
    profile: {
      userId: 'test_user_id',
      avatarUrl: '',
      nickname: '',
      gender: '',
      birthday: '',
      age: 0
    }
  },

  onShow() {
    this.loadProfile()
  },

  methods: {
    loadProfile() {
      let stored: any = wx.getStorageSync('USER_PROFILE')

      if (typeof stored === 'string') {
        try {
          stored = JSON.parse(stored)
        } catch (err) {
          stored = {}
        }
      }

      const profile = {
        userId: 'test_user_id',
        avatarUrl: '',
        nickname: '',
        gender: 'unknown',
        birthday: '',
        age: 0,
        ...stored
      }

      console.log('mine 页面读取 USER_PROFILE:', profile)

      this.setData({
        profile
      })
    },

    onEditProfile() {
      console.log('点击了完善资料按钮')
      wx.navigateTo({
        url: '/pages/profile/edit',
        success: () => {
          console.log('跳转完善资料页面成功')
        },
        fail: (err) => {
          console.error('跳转完善资料页面失败', err)
          wx.showToast({
            title: '页面跳转失败',
            icon: 'none'
          })
        }
      })
    },

    onNavigateToPersonalData() {
      wx.switchTab({
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
    }
  }
})
