import { completePointsTask } from '../../utils/points-store'

const API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'

type DoctorOption = {
  id: string
  name: string
  department: string
  tags: string[]
}

type ReportImage = {
  url: string
  name: string
}

const MAX_REPORT_IMAGES = 9

const REPORT_TYPE_OPTIONS = ['血常规', 'B超', '激素六项', '其他']

function getFileName(filePath: string) {
  return filePath.split('/').pop() || filePath.split('\\').pop() || '本地文件'
}

function canSubmitWithState(data: {
  selectedDoctor: DoctorOption | null
  reportImages: ReportImage[]
  selectedReportType: string
  remark: string
}) {
  const hasDoctor = Boolean(data.selectedDoctor)
  const hasImages = data.reportImages.length > 0
  const hasType = Boolean(data.selectedReportType)

  if (data.selectedReportType === '其他') {
    return hasDoctor && hasImages && hasType && Boolean(data.remark.trim())
  }

  return hasDoctor && hasImages && hasType
}

Component({
  data: {
    doctorOptions: [] as DoctorOption[],
    doctorPickerRange: [] as string[],
    doctorPickerIndex: 0,
    selectedDoctor: null as DoctorOption | null,
    selectedDoctorText: '' as string,
    reportImages: [] as ReportImage[],
    maxReportImages: MAX_REPORT_IMAGES,
    canSubmit: false,
    reportTypeOptions: REPORT_TYPE_OPTIONS,
    selectedReportType: '' as string,
    remark: '' as string
  },
  lifetimes: {
    attached() {
      this.loadDoctorOptions()
    }
  },
  methods: {
    async loadDoctorOptions() {
      try {
        const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
          wx.request({
            url: `${API_BASE_URL}/api/doctors/list`,
            method: 'GET',
            success: resolve,
            fail: reject
          })
        })

        if (response.statusCode === 200 && response.data) {
          const responseData = response.data as any
          const doctors = Array.isArray(responseData?.data) ? responseData.data.map((item: any) => {
            const doctorName = String(item.doctorName || item.display_name || item.displayName || item.name || '').trim()
            const department = String(item.department || '').trim()
            const title = String(item.title || '').trim()
            const tags = [title, department].filter(Boolean)

            return {
              id: String(item.doctorId || item.id || ''),
              name: doctorName || String(item.doctorId || item.id || ''),
              department,
              tags
            }
          }) : []

          this.setData({
            doctorOptions: doctors,
            doctorPickerRange: doctors.map((doctor) => `${doctor.name} ${doctor.department ? '· ' + doctor.department : ''}`)
          })
        }
      } catch (error) {
        console.error('[report-upload] 加载医生列表失败:', error)
      }
    },
    onDoctorPickerChange(event: WechatMiniprogram.CustomEvent) {
      console.log('[doctor-select] upload report doctor picker changed')
      const index = Number(event.detail?.value ?? -1)
      console.log('[doctor-select] selected index:', index)

      if (Number.isNaN(index) || index < 0 || index >= this.data.doctorOptions.length) {
        console.error('[doctor-select] invalid index:', index)
        return
      }

      const selectedDoctor = this.data.doctorOptions[index]
      console.log('[doctor-select] selectedDoctor:', selectedDoctor)

      const selectedDoctorText = selectedDoctor
        ? `${selectedDoctor.name}${selectedDoctor.department ? ' · ' + selectedDoctor.department : ''}`
        : ''

      this.setData({
        doctorPickerIndex: index,
        selectedDoctor,
        selectedDoctorText,
        canSubmit: canSubmitWithState({
          selectedDoctor,
          reportImages: this.data.reportImages,
          selectedReportType: this.data.selectedReportType,
          remark: this.data.remark
        })
      })
    },
    onChooseReportType() {
      wx.showActionSheet({
        itemList: this.data.reportTypeOptions,
        success: (res) => {
          const selectedReportType = this.data.reportTypeOptions[res.tapIndex] || ''

          this.setData({
            selectedReportType,
            canSubmit: canSubmitWithState({
              selectedDoctor: this.data.selectedDoctor,
              reportImages: this.data.reportImages,
              selectedReportType,
              remark: this.data.remark
            })
          })
        }
      })
    },
    onRemarkInput(event: WechatMiniprogram.Input) {
      const remark = event.detail.value

      this.setData({
        remark,
        canSubmit: canSubmitWithState({
          selectedDoctor: this.data.selectedDoctor,
          reportImages: this.data.reportImages,
          selectedReportType: this.data.selectedReportType,
          remark
        })
      })
    },
    onChooseReportImages() {
      const remainCount = MAX_REPORT_IMAGES - this.data.reportImages.length

      if (remainCount <= 0) {
        wx.showToast({
          title: '最多上传 9 张图片',
          icon: 'none'
        })
        return
      }

      wx.chooseMedia({
        count: remainCount,
        mediaType: ['image'],
        sourceType: ['album', 'camera'],
        sizeType: ['compressed'],
        success: (res) => {
          const nextImages = res.tempFiles.map((file) => ({
            url: file.tempFilePath,
            name: getFileName(file.tempFilePath)
          }))

          if (!nextImages.length) {
            return
          }

          const reportImages = [...this.data.reportImages, ...nextImages].slice(0, MAX_REPORT_IMAGES)

          this.setData({
            reportImages,
            canSubmit: canSubmitWithState({
              selectedDoctor: this.data.selectedDoctor,
              reportImages,
              selectedReportType: this.data.selectedReportType,
              remark: this.data.remark
            })
          })
        }
      })
    },
    onPreviewReportImage(event: WechatMiniprogram.CustomEvent) {
      const current = event.currentTarget.dataset.url as string

      if (!current) {
        return
      }

      wx.previewImage({
        current,
        urls: this.data.reportImages.map((item) => item.url)
      })
    },
    onRemoveReportImage(event: WechatMiniprogram.CustomEvent) {
      const index = Number(event.currentTarget.dataset.index)

      if (Number.isNaN(index)) {
        return
      }

      const reportImages = this.data.reportImages.filter((_, itemIndex) => itemIndex !== index)

      this.setData({
        reportImages,
        canSubmit: canSubmitWithState({
          selectedDoctor: this.data.selectedDoctor,
          reportImages,
          selectedReportType: this.data.selectedReportType,
          remark: this.data.remark
        })
      })
    },
    validateForm() {
      if (!this.data.selectedDoctor) {
        return '请先确认医生信息'
      }

      if (!this.data.reportImages.length) {
        return '请上传报告图片'
      }

      if (!this.data.selectedReportType) {
        return '请选择报告类型'
      }

      if (this.data.selectedReportType === '其他' && !this.data.remark.trim()) {
        return '选择"其他"类型时，请填写报告备注'
      }

      return ''
    },
    onSubmit() {
      const validationMessage = this.validateForm()

      if (validationMessage) {
        wx.showToast({
          title: validationMessage,
          icon: 'none'
        })
        return
      }

      this.submitReport()
    },

    async submitReport() {
      wx.showLoading({
        title: '提交中...',
        mask: true
      })

      try {
        // 使用 ensureUserId 确保获取到 userId
        const userId = await this.ensureUserId()
        
        if (!userId) {
          wx.hideLoading()
          wx.showToast({
            title: '登录失败，请稍后重试',
            icon: 'none'
          })
          return
        }

        const reportId = await this.createReport(userId as number)
        await this.uploadImages(reportId, userId as number)
        await this.completeReport(reportId, userId as number)

        wx.hideLoading()
        wx.showToast({
          title: '报告已提交',
          icon: 'success'
        })
        completePointsTask('report_upload')
        
        // 设置默认 tab 为检查报告，然后跳转到我的数据页面
        wx.setStorageSync('DATA_DEFAULT_TAB', 'report')
        
        setTimeout(() => {
          // 我的数据页面不是 tabBar 页面，使用 redirectTo
          wx.redirectTo({
            url: '/pages/personal-data/index'
          })
        }, 1500)
      } catch (error) {
        wx.hideLoading()
        wx.showToast({
          title: error instanceof Error ? error.message : (error as string) || '提交失败',
          icon: 'none',
          duration: 3000
        })
      }
    },

    getUserId(): string | number | null {
      const app = getApp<IAppOption>()
      const globalData = app.globalData || {}
      
      // 调试：打印所有可能的 userId 来源
      const globalUserId = globalData.userId
      const storageUserId = wx.getStorageSync('USER_ID')
      const profileStorage = wx.getStorageSync('USER_PROFILE')
      const profileData = typeof profileStorage === 'string' ? JSON.parse(profileStorage || '{}') : (profileStorage || {})
      const profileUserId = profileData.userId
      
      console.log('[report-upload] 调试 - app.globalData.userId:', globalUserId)
      console.log('[report-upload] 调试 - wx.getStorageSync(USER_ID):', storageUserId)
      console.log('[report-upload] 调试 - wx.getStorageSync(USER_PROFILE):', JSON.stringify(profileData))
      
      // 严格按照顺序获取 userId
      let userId: string | number | null = null
      
      // 1. app.globalData.userId
      if (globalUserId) {
        userId = globalUserId
        console.log('[report-upload] getUserId 从 globalData.userId 获取:', userId)
      }
      // 2. wx.getStorageSync('USER_ID')
      else if (storageUserId) {
        userId = storageUserId
        console.log('[report-upload] getUserId 从 USER_ID 缓存获取:', userId)
      }
      // 3. wx.getStorageSync('USER_PROFILE').userId
      else if (profileUserId) {
        userId = profileUserId
        console.log('[report-upload] getUserId 从 USER_PROFILE.userId 获取:', userId)
      }
      
      return userId || null
    },
    
    async ensureUserId(): Promise<string | number | null> {
      const app = getApp<IAppOption>()
      
      // 先尝试获取 userId
      let userId = this.getUserId()
      
      // 如果已有 userId，直接返回
      if (userId) {
        return userId
      }
      
      // 如果没有 userId，尝试等待登录完成
      console.log('[report-upload] 未找到 userId，等待登录完成...')
      
      return new Promise((resolve) => {
        // 如果正在登录中，注册回调
        if (app.globalData.isLoggingIn || app.globalData.loginPromise) {
          app.registerLoginCallback((user: any) => {
            const newUserId = user.userId || user.id
            console.log('[report-upload] 登录完成，获取到 userId:', newUserId)
            resolve(newUserId || null)
          })
        } else {
          // 如果没有登录中，尝试重新登录
          console.log('[report-upload] 尝试重新启动登录流程...')
          app.startLogin()
          
          // 等待登录完成
          app.registerLoginCallback((user: any) => {
            const newUserId = user.userId || user.id
            console.log('[report-upload] 重新登录完成，获取到 userId:', newUserId)
            resolve(newUserId || null)
          })
        }
      })
    },

    createReport(userId: number): Promise<number> {
      return new Promise((resolve, reject) => {
        const doctor = this.data.selectedDoctor
        if (!doctor) {
          reject('请先选择医生')
          return
        }

        wx.request({
          url: `${API_BASE_URL}/api/report/create`,
          method: 'POST',
          header: {
            'Content-Type': 'application/json'
          },
          data: {
            userId: userId,
            doctorId: doctor.id,
            doctorName: doctor.name,
            doctorDepartment: doctor.department,
            reportType: this.data.selectedReportType || '检查报告',
            remark: this.data.remark
          },
          success: (res) => {
            if (res.statusCode === 200 && res.data && (res.data as any).success) {
              const reportId = (res.data as any).data.reportId
              resolve(reportId)
            } else {
              const errorMsg = (res.data as any)?.error || '创建报告失败'
              reject(errorMsg)
            }
          },
          fail: () => {
            reject('网络错误，请检查网络连接')
          }
        })
      })
    },

    uploadImages(reportId: number, userId: number): Promise<number> {
      return new Promise((resolve, reject) => {
        const images = this.data.reportImages
        if (images.length === 0) {
          reject('请上传报告图片')
          return
        }

        let uploadedCount = 0
        const totalCount = images.length

        const uploadNext = (index: number) => {
          if (index >= totalCount) {
            resolve(reportId)
            return
          }

          wx.showLoading({
            title: `上传中 ${uploadedCount + 1}/${totalCount}`,
            mask: true
          })

          wx.uploadFile({
            url: `${API_BASE_URL}/api/report/file/upload`,
            filePath: images[index].url,
            name: 'file',
            formData: {
              reportId: String(reportId),
              userId: String(userId),
              sortOrder: String(index)
            },
            success: (res) => {
              try {
                const data = JSON.parse(res.data)
                if (res.statusCode === 200 && data.success) {
                  uploadedCount++
                  uploadNext(index + 1)
                } else {
                  reject(data.error || `第 ${index + 1} 张图片上传失败`)
                }
              } catch (e) {
                reject('上传响应解析失败')
              }
            },
            fail: () => {
              reject(`第 ${index + 1} 张图片上传失败，请检查网络`)
            }
          })
        }

        uploadNext(0)
      })
    },

    completeReport(reportId: number, userId: number): Promise<void> {
      return new Promise((resolve, reject) => {
        wx.request({
          url: `${API_BASE_URL}/api/report/complete`,
          method: 'POST',
          header: {
            'Content-Type': 'application/json'
          },
          data: {
            reportId: reportId,
            userId: userId
          },
          success: (res) => {
            if (res.statusCode === 200 && res.data && (res.data as any).success) {
              resolve()
            } else {
              const errorMsg = (res.data as any)?.error || '完成报告失败'
              reject(errorMsg)
            }
          },
          fail: () => {
            reject('网络错误，请检查网络连接')
          }
        })
      })
    }
  }
})
