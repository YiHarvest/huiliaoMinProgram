import { expertProfiles } from '../../data/experts'

type DoctorOption = {
  id: string
  name: string
  department: string
  tags: string[]
}

type GenderOption = 'male' | 'female'

type CategoryOption = {
  key: string
  name: string
}

type ScaleItem = {
  id: string
  templateId: string
  questionnaireName: string
  description: string
}

const doctorOptions: DoctorOption[] = expertProfiles.slice(0, 4).map((expert) => ({
  id: expert.id,
  name: expert.name,
  department: expert.department,
  tags: expert.focus.slice(0, 2)
}))

function buildStatePatch(data: {
  selectedDoctor: DoctorOption | null
  selectedGender: GenderOption | null
  scaleList: ScaleItem[]
}) {
  return {
    canShowScales: true,
    visibleScales: data.scaleList
  }
}

Component({
  data: {
    doctorOptions,
    scaleList: [] as ScaleItem[],
    genderOptions: [
      { value: 'male', label: '男' },
      { value: 'female', label: '女' }
    ] as Array<{ value: GenderOption; label: string }>,
    selectedDoctor: null as DoctorOption | null,
    selectedGender: null as GenderOption | null,
    canShowScales: false,
    visibleScales: [] as ScaleItem[],
    isLoading: false
  },
  lifetimes: {
    attached() {
      this.loadScaleOptions()
    }
  },
  methods: {
    loadScaleOptions() {
      this.setData({
        isLoading: true
      })

      const openid = wx.getStorageSync('openid') || 'test_user_id'
      wx.request({
        url: 'https://miniprogram.huiliaoyiyuan.com/api/questionnaires/options',
        method: 'GET',
        data: { externalUserId: openid },
        success: (res) => {
          if (res.statusCode === 200) {
            const responseData = res.data as any
            
            const categories = (responseData && responseData.categories) || []
            const scales = (responseData && responseData.scales) || []

            // 增加数据量限制，防止后端返回过多数据
            const MAX_SCALES_THRESHOLD = 500
            const MAX_RENDER_SCALES = 100
            
            // 如果数据量过大，直接显示错误提示
            if (scales.length > MAX_SCALES_THRESHOLD) {
              this.setData({
                isLoading: false
              })
              wx.showToast({
                title: '数据异常，请联系管理员',
                icon: 'none'
              })
              return
            }
            
            const limitedScales = scales.length > MAX_RENDER_SCALES 
              ? scales.slice(0, MAX_RENDER_SCALES) 
              : scales

            const seenTemplateIds = new Set<string>()
            const uniqueScales = limitedScales.filter((scale: any) => {
              const templateId = String(scale.templateId || scale.id)
              if (seenTemplateIds.has(templateId)) {
                return false
              }
              seenTemplateIds.add(templateId)
              return true
            })

            const scaleList = Array.isArray(uniqueScales) ? uniqueScales.map(item => ({
              id: String(item.templateId || item.id || ''),
              templateId: String(item.templateId || ''),
              questionnaireName: item.questionnaireName || item.name || '',
              description: item.description || ''
            })) : []

            // 排序：将包含"第一次填表"或"首次填写"的量表优先排到最前面
            scaleList.sort((a, b) => {
              const aHasKey = a.questionnaireName.includes('第一次填表') || a.questionnaireName.includes('首次填写')
              const bHasKey = b.questionnaireName.includes('第一次填表') || b.questionnaireName.includes('首次填写')
              if (aHasKey && !bHasKey) return -1
              if (!aHasKey && bHasKey) return 1
              return 0 // 保持原有相对顺序
            })

            const statePatch = buildStatePatch({
              selectedDoctor: this.data.selectedDoctor,
              selectedGender: this.data.selectedGender,
              scaleList
            })

            const patchObject = {
              categoryOptions: categories,
              scaleList,
              visibleScales: statePatch.visibleScales,
              canShowScales: statePatch.canShowScales,
              isLoading: false
            }

            this.setData(patchObject)

            return
          }

          this.setData({
            isLoading: false
          })
          wx.showToast({
            title: '加载量表数据失败',
            icon: 'none'
          })
        },
        fail: () => {
          this.setData({
            isLoading: false
          })
          wx.showToast({
            title: '网络错误，请稍后重试',
            icon: 'none'
          })
        }
      })
    },
    onChooseDoctor() {
      wx.showActionSheet({
        itemList: this.data.doctorOptions.map((doctor) => `${doctor.name} · ${doctor.department}`),
        success: (res) => {
          const selectedDoctor = this.data.doctorOptions[res.tapIndex] || null

          this.setData({
            selectedDoctor,
            ...buildStatePatch({
              selectedDoctor,
              selectedGender: this.data.selectedGender,
              scaleList: this.data.scaleList
            })
          })
        }
      })
    },
    onSelectGender(event: WechatMiniprogram.CustomEvent) {
      const selectedGender = event.currentTarget.dataset.value as GenderOption

      if (!selectedGender) {
        return
      }

      this.setData({
        selectedGender,
        ...buildStatePatch({
          selectedDoctor: this.data.selectedDoctor,
          selectedGender,
          scaleList: this.data.scaleList
        })
      })
    },

    validateBeforeStart() {
      if (!this.data.selectedDoctor) {
        return '请先确认医生信息'
      }

      if (!this.data.selectedGender) {
        return '请选择性别'
      }

      return ''
    },
    async onStartScale(event: WechatMiniprogram.CustomEvent) {
      const validationMessage = this.validateBeforeStart()

      if (validationMessage) {
        wx.showToast({
          title: validationMessage,
          icon: 'none'
        })
        return
      }

      // 直接使用字符串形式的templateId（微信小程序会自动将kebab-case转换为camelCase）
      const templateId = String(event.currentTarget.dataset.templateId || '')
      const questionnaireName = event.currentTarget.dataset.name as string
      
      // 检查templateId是否有效
      if (!templateId || templateId.trim() === '') {
        wx.showToast({
          title: '量表模板ID无效',
          icon: 'none'
        })
        return
      }

      const openid = wx.getStorageSync('openid') || 'test_user_id'
      const externalUserId = openid
      const payload = { externalUserId, templateId }
      
      try {
        // 使用Promise包装wx.request
        const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
          wx.request({
            url: 'https://miniprogram.huiliaoyiyuan.com/api/questionnaires/start',
            method: 'POST',
            data: payload,
            success: resolve,
            fail: reject
          })
        })

        if (response.statusCode === 200 && response.data) {
          // 添加类型断言，明确response.data的结构
          const data = response.data as { recordId?: number }
          const recordId = data.recordId
          if (recordId) {
            wx.showToast({
              title: `开始填写${questionnaireName}`,
              icon: 'success'
            })
            // 跳转到问卷填写页面
            const url = `/pages/questionnaire/questionnaire?recordId=${recordId}`
            wx.navigateTo({
              url,
              fail: (err) => {
                wx.showToast({
                  title: '页面跳转失败',
                  icon: 'none'
                })
              }
            })
          } else {
            wx.showToast({
              title: '获取记录ID失败',
              icon: 'none'
            })
          }
        } else {
          wx.showToast({
            title: '开始填写失败',
            icon: 'none'
          })
        }
      } catch (error) {
        wx.showToast({
          title: '网络错误，请稍后重试',
          icon: 'none'
        })
      }
    }
  }
})
