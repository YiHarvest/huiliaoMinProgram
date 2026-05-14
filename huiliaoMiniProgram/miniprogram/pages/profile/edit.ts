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

  async loadProfile() {
    try {
      // 先从本地缓存获取基础信息
      let stored = wx.getStorageSync('USER_PROFILE')
      if (typeof stored === 'string') {
        stored = JSON.parse(stored || '{}')
      }
      
      const userId = stored?.userId || stored?.id || wx.getStorageSync('USER_ID') || wx.getStorageSync('userId')
      
      // 如果有 userId，尝试从后端获取最新资料
      if (userId) {
        try {
          wx.showLoading({ title: '加载中...', mask: false })
          
          const response: any = await new Promise((resolve, reject) => {
            wx.request({
              url: `https://miniprogram.huiliaoyiyuan.com/api/user/profile?userId=${userId}`,
              method: 'GET',
              success(res) { resolve(res) },
              fail(err) { reject(err) }
            })
          })
          
          wx.hideLoading()
          
          if (response.statusCode === 200 && response.data && response.data.success) {
            const serverProfile = response.data.data
            console.log('[edit] 后端返回 profile:', serverProfile)
            
            // 合并服务器数据和本地缓存
            const birthday = serverProfile.birthday || stored.birthday || ''
            
            // 手机号优先显示真实值，没有则显示脱敏值
            const phone = serverProfile.phone || serverProfile.phoneMasked || stored.phone || stored.phoneMasked || ''
            const phoneMasked = serverProfile.phoneMasked || stored.phoneMasked || ''
            
            // 身份证号不显示完整值，只显示脱敏值
            const idCardMasked = serverProfile.idCardMasked || stored.idCardMasked || ''
            
            this.setData({
              profile: {
                userId: serverProfile.userId || serverProfile.id || userId,
                userCode: serverProfile.userCode || stored.userCode || wx.getStorageSync('USER_CODE') || '',
                avatarUrl: serverProfile.avatarUrl || stored.avatarUrl || '',
                nickname: serverProfile.nickname || stored.nickname || '',
                gender: serverProfile.gender || stored.gender || '',
                birthday: birthday,
                phone: phone,
                phoneMasked: phoneMasked,
                idCard: '',  // 不回显完整身份证号
                idCardMasked: idCardMasked,
                createdAt: serverProfile.createdAt || stored.createdAt || Date.now(),
                updatedAt: serverProfile.updatedAt || stored.updatedAt || Date.now()
              },
              originalProfile: {
                phone: phone,  // 保存原始显示值，用于判断是否修改
                phoneMasked: phoneMasked,
                idCardMasked: idCardMasked
              },
              hasChanged: false,
              age: this.calculateAge(birthday)
            })
            
            return
          }
        } catch (error) {
          console.error('[edit] 从后端加载 profile 失败:', error)
          wx.hideLoading()
        }
      }
      
      // 没有 userId 或后端请求失败，使用本地缓存
      if (stored && Object.keys(stored).length > 0) {
        const profile = stored
        const birthday = profile.birthday || ''
        console.log('[edit] 使用本地缓存 USER_PROFILE:', profile)
        
        const phone = profile.phone || profile.phoneMasked || ''
        const phoneMasked = profile.phoneMasked || ''
        const idCardMasked = profile.idCardMasked || ''
        
        this.setData({
          profile: {
            userId: profile.userId || profile.id || 0,
            userCode: profile.userCode || wx.getStorageSync('USER_CODE') || '',
            avatarUrl: profile.avatarUrl || '',
            nickname: profile.nickname || '',
            gender: profile.gender || '',
            birthday: birthday,
            phone: phone,
            phoneMasked: phoneMasked,
            idCard: '',
            idCardMasked: idCardMasked,
            createdAt: profile.createdAt || Date.now(),
            updatedAt: profile.updatedAt || Date.now()
          },
          originalProfile: {
            phone: phone,
            phoneMasked: phoneMasked,
            idCardMasked: idCardMasked
          },
          hasChanged: false,
          age: this.calculateAge(birthday)
        })
      } else {
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

    // 构建保存数据，注意不要把脱敏值当成真实值保存
    const currentPhone = this.data.profile.phone || ''
    const currentIdCard = this.data.profile.idCard || ''
    const originalPhone = this.data.originalProfile.phone || ''
    
    // 判断手机号是否被真正修改（不是脱敏值）
    // 如果当前手机号和原始显示值相同且包含 *，说明是脱敏值，用户没有真正修改
    const isPhoneModified = currentPhone !== originalPhone || !currentPhone.includes('*')
    
    // 判断身份证号是否被真正修改（完整18位）
    // 身份证号输入框只允许输入数字和X，所以如果不是完整18位，说明没有真正修改
    const isIdCardModified = currentIdCard.length === 18
    
    // 保存前打印旧缓存
    const oldProfileBeforeSave = wx.getStorageSync('USER_PROFILE') || {}
    console.log('[profile/save] 保存前 USER_PROFILE =', {
      phone: oldProfileBeforeSave.phone,
      phoneMasked: oldProfileBeforeSave.phoneMasked,
      idCardMasked: oldProfileBeforeSave.idCardMasked,
      hasPhoneMasked: !!oldProfileBeforeSave.phoneMasked,
      hasIdCardMasked: !!oldProfileBeforeSave.idCardMasked
    })
    
    const profileData: any = {
      userId: userId,
      nickname: nickname,
      gender: this.data.profile.gender || oldProfile.gender || 'unknown',
      birthday: this.data.profile.birthday || oldProfile.birthday || '',
      avatarUrl: avatarUrl
    }
    
    // 只有真正修改了手机号才传递
    if (isPhoneModified && currentPhone) {
      profileData.phone = currentPhone
    }
    
    // 只有真正输入了完整18位身份证才传递
    if (isIdCardModified) {
      profileData.idCard = currentIdCard
    }
    
    // 打印提交给后端的数据
    console.log('[profile/save] 提交给后端 profileData =', {
      userId: profileData.userId,
      nickname: profileData.nickname,
      gender: profileData.gender,
      birthday: profileData.birthday,
      avatarUrl: profileData.avatarUrl,
      hasPhone: !!profileData.phone,
      hasIdCard: !!profileData.idCard,
      phone: profileData.phone ? '***' : undefined,
      idCard: profileData.idCard ? '***' : undefined
    })
    
    console.log('[edit] isPhoneModified:', isPhoneModified, 'currentPhone:', currentPhone)
    console.log('[edit] isIdCardModified:', isIdCardModified, 'currentIdCard:', currentIdCard)

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
      
      // 重点打印后端返回的敏感信息字段
      console.log('[profile/save] 后端返回 data =', response?.data)
      console.log('[profile/save] 后端返回 phoneMasked =', response?.data?.data?.phoneMasked)
      console.log('[profile/save] 后端返回 idCardMasked =', response?.data?.data?.idCardMasked)

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
        // 保存成功后，重新从后端获取完整资料，避免后端返回值不完整
        wx.showLoading({ title: '刷新资料...' })
        
        try {
          const refreshResponse: any = await new Promise((resolve, reject) => {
            wx.request({
              url: `https://miniprogram.huiliaoyiyuan.com/api/user/profile?userId=${userId}`,
              method: 'GET',
              success(res) { resolve(res) },
              fail(err) { reject(err) }
            })
          })
          
          wx.hideLoading()
          
          if (refreshResponse.statusCode === 200 && refreshResponse.data?.success) {
            const serverProfile = refreshResponse.data.data
            const oldProfile = wx.getStorageSync('USER_PROFILE') || {}
            
            // 合并数据：优先使用后端返回的，但保留旧值作为兜底
            const phone = serverProfile.phone || serverProfile.phoneMasked || oldProfile.phone || oldProfile.phoneMasked || ''
            const phoneMasked = serverProfile.phoneMasked || oldProfile.phoneMasked || ''
            const idCardMasked = serverProfile.idCardMasked || oldProfile.idCardMasked || ''
            
            const updatedProfile = {
              ...oldProfile,
              ...serverProfile,
              userId: serverProfile.userId || serverProfile.id || userId,
              userCode: serverProfile.userCode || oldProfile.userCode || wx.getStorageSync('USER_CODE') || '',
              openid: oldProfile.openid || '',
              unionid: oldProfile.unionid || '',
              nickname: this.data.profile.nickname,
              gender: this.data.profile.gender || oldProfile.gender || 'unknown',
              birthday: this.data.profile.birthday,
              avatarUrl: this.data.profile.avatarUrl,
              // 敏感信息处理
              phone: phone,
              phoneMasked: phoneMasked,
              idCard: '',  // 不回显完整身份证号
              idCardMasked: idCardMasked,
              updatedAt: Date.now()
            }

            // 更新所有缓存
            wx.setStorageSync('USER_PROFILE', updatedProfile)
            wx.setStorageSync('USER_ID', updatedProfile.userId)
            wx.setStorageSync('USER_CODE', updatedProfile.userCode)
            
            // 更新全局数据
            const app = getApp<IAppOption>()
            app.globalData.userProfile = updatedProfile
            app.globalData.userId = updatedProfile.userId
            app.globalData.userCode = updatedProfile.userCode
            
            // 打印最终写入的数据
            console.log('[profile/save] 最终写入 USER_PROFILE =', {
              phone: updatedProfile.phone,
              phoneMasked: updatedProfile.phoneMasked,
              idCardMasked: updatedProfile.idCardMasked,
              userId: updatedProfile.userId,
              nickname: updatedProfile.nickname
            })
            console.log('[profile/save] 最终写入 globalData.userProfile =', {
              phone: app.globalData.userProfile?.phone,
              phoneMasked: app.globalData.userProfile?.phoneMasked,
              idCardMasked: app.globalData.userProfile?.idCardMasked,
              userId: app.globalData.userId
            })
            
            console.log('[edit] 保存后刷新资料成功:', updatedProfile)

            this.setData({
              profile: updatedProfile,
              originalProfile: {
                phone: phone,
                phoneMasked: phoneMasked,
                idCardMasked: idCardMasked
              },
              hasChanged: false,
              isSaved: true
            })

            // 更新上一页数据（通过 eventChannel + 方法调用双重保障）
            const pages = getCurrentPages()
            const prevPage: any = pages[pages.length - 2]
            
            // 方式1：通过 eventChannel 通知（推荐）
            try {
              const eventChannel = this.getOpenerEventChannel()
              if (eventChannel && typeof eventChannel.emit === 'function') {
                eventChannel.emit('profileUpdated', updatedProfile)
                console.log('[edit] 已通过 eventChannel 发送 profileUpdated 事件')
              }
            } catch (e) {
              console.warn('[edit] eventChannel emit 失败:', e)
            }
            
            // 方式2：直接调用上一页方法（兼容旧逻辑）
            if (prevPage && typeof prevPage.loadUserProfile === 'function') {
              prevPage.loadUserProfile()
              console.log('[edit] 已调用 prevPage.loadUserProfile()')
            } else if (prevPage) {
              prevPage.setData({
                profile: updatedProfile
              })
              console.log('[edit] 已通过 setData 更新上一页')
            }

            wx.hideLoading()
            wx.showToast({
              title: '保存成功',
              icon: 'success'
            })
          } else {
            // 刷新失败，使用本地数据
            console.warn('[edit] 刷新资料失败，使用本地数据')
            const oldProfile = wx.getStorageSync('USER_PROFILE') || {}
            
            // 更新上一页数据
            const pages = getCurrentPages()
            const prevPage: any = pages[pages.length - 2]
            if (prevPage && typeof prevPage.loadProfile === 'function') {
              prevPage.loadProfile()
            }

            this.setData({
              hasChanged: false,
              isSaved: true
            })

            wx.hideLoading()
            wx.showToast({
              title: '保存成功',
              icon: 'success'
            })
          }
        } catch (refreshError) {
          wx.hideLoading()
          console.error('[edit] 刷新资料失败:', refreshError)
          
          // 更新上一页数据
          const pages = getCurrentPages()
          const prevPage: any = pages[pages.length - 2]
          if (prevPage && typeof prevPage.loadProfile === 'function') {
            prevPage.loadProfile()
          }

          this.setData({
            hasChanged: false,
            isSaved: true
          })

          wx.showToast({
            title: '保存成功',
            icon: 'success'
          })
        }

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