import { expertProfiles } from '../../data/experts'

console.log('=== NEW SCALE-FORM CODE LOADED 2026-04-22 ===')

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

function getScaleFormDebugSnapshot(data: Record<string, any>) {
  return {
    selectedDoctor: data.selectedDoctor,
    selectedGender: data.selectedGender,
    selectedCategory: data.selectedCategory,
    categoryOptions: data.categoryOptions,
    templates: data.templates,
    scaleList: data.scaleList,
    visibleScales: data.visibleScales,
    displayTemplates: data.displayTemplates,
    filteredTemplates: data.filteredTemplates,
    debugLastAction: data.debugLastAction
  }
}

function logScaleFormRenderSource(data: Record<string, any>) {
  console.log('[scale-form:render-source] current render field = visibleScales', data.visibleScales)
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
    isLoading: false,
    debugLastAction: ''
  },
  lifetimes: {
    attached() {
      console.log('[scale-form:onLoad] data snapshot', getScaleFormDebugSnapshot(this.data as Record<string, any>))
      logScaleFormRenderSource(this.data as Record<string, any>)
      this.loadScaleOptions()
    }
  },
  pageLifetimes: {
    show() {
      console.log('[scale-form:onShow] data snapshot', getScaleFormDebugSnapshot(this.data as Record<string, any>))
      logScaleFormRenderSource(this.data as Record<string, any>)
    }
  },
  methods: {
    loadScaleOptions() {
      this.setData({
        isLoading: true,
        debugLastAction: 'loadScaleOptions:start'
      })

      const openid = wx.getStorageSync('openid') || 'test_user_id'
      wx.request({
        url: 'https://miniprogram.huiliaoyiyuan.com/api/questionnaires/options',
        method: 'GET',
        data: { externalUserId: openid },
        success: (res) => {
          console.log('questionnaire raw response', res)
          console.log('questionnaire response data', res.data)
          console.log('questionnaire statusCode', res.statusCode)

          if (res.statusCode === 200) {
            const responseData = res.data as any
            
            // 1. 原始接口响应
            console.log('[scale-form:stage1] 原始接口响应 scales.length:', (responseData && responseData.scales && responseData.scales.length) || 0)
            console.log('[scale-form:stage1] 原始接口响应前3条:', (responseData && responseData.scales && responseData.scales.slice(0, 3)) || [])
            
            const categories = (responseData && responseData.categories) || []
            const scales = (responseData && responseData.scales) || []

            // 2. 归一化后
            const normalizedScales = scales
            console.log('[scale-form:stage2] 归一化后 normalizedScales.length:', normalizedScales.length)
            console.log('[scale-form:stage2] 归一化后前3条:', normalizedScales.slice(0, 3))

            // 找到不育症诊断量表
            const testScale = scales.find((scale: any) => scale.questionnaireName.includes('不育症诊断量表'))
            console.log('[step 1] 原始 response.data - 不育症诊断量表:', {
              questionnaireName: testScale && testScale.questionnaireName,
              templateId: testScale && testScale.templateId,
              id: testScale && testScale.id,
              scale: testScale
            })

            console.log('[scale-form:request-success] categories', categories)
            console.log('[scale-form:request-success] scales.length', scales.length)
            console.log('[scale-form:request-success] scales[0]', scales[0])

            // 按 templateId 去重，只保留每个 templateId 的第一条
            console.log('[step 2] uniqueScales 生成前 - 不育症诊断量表:', {
              questionnaireName: testScale && testScale.questionnaireName,
              templateId: testScale && testScale.templateId,
              id: testScale && testScale.id,
              scale: testScale
            })

            // 增加数据量限制，防止后端返回过多数据
            const MAX_SCALES_THRESHOLD = 500
            const MAX_RENDER_SCALES = 100
            
            // 如果数据量过大，直接显示错误提示
            if (scales.length > MAX_SCALES_THRESHOLD) {
              console.error('[scale-form:error] 数据量过大，后端返回了', scales.length, '条数据，超过阈值', MAX_SCALES_THRESHOLD)
              this.setData({
                isLoading: false,
                debugLastAction: 'loadScaleOptions:data-too-large'
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
            console.log('[scale-form:debug] limitedScales.length', limitedScales.length)

            const seenTemplateIds = new Set<string>()
            const uniqueScales = limitedScales.filter((scale: any) => {
              const templateId = String(scale.templateId || scale.id)
              if (seenTemplateIds.has(templateId)) {
                return false
              }
              seenTemplateIds.add(templateId)
              return true
            })

            // 3. 去重后
            console.log('[scale-form:stage3] 去重后 uniqueScales.length:', uniqueScales.length)
            console.log('[scale-form:stage3] 去重后前3条:', uniqueScales.slice(0, 3))

            // 找到去重后的不育症诊断量表
            const testUniqueScale = uniqueScales.find((scale: any) => scale.questionnaireName.includes('不育症诊断量表'))
            console.log('[step 3] uniqueScales 生成后 - 不育症诊断量表:', {
              questionnaireName: testUniqueScale && testUniqueScale.questionnaireName,
              templateId: testUniqueScale && testUniqueScale.templateId,
              id: testUniqueScale && testUniqueScale.id,
              scale: testUniqueScale
            })

            console.log('[scale-form:request-success] uniqueScales.length', uniqueScales.length)

            const scaleList = Array.isArray(uniqueScales) ? uniqueScales.map(item => ({
              id: String(item.templateId || item.id || ''),
              templateId: String(item.templateId || ''),
              questionnaireName: item.questionnaireName || item.name || '',
              description: item.description || ''
            })) : []

            // 5. 排序：将包含"第一次填表"或"首次填写"的量表优先排到最前面
            scaleList.sort((a, b) => {
              const aHasKey = a.questionnaireName.includes('第一次填表') || a.questionnaireName.includes('首次填写')
              const bHasKey = b.questionnaireName.includes('第一次填表') || b.questionnaireName.includes('首次填写')
              if (aHasKey && !bHasKey) return -1
              if (!aHasKey && bHasKey) return 1
              return 0 // 保持原有相对顺序
            })

            // 4. setData 前
            console.log('[scale-form:stage4] setData 前 scaleList.length:', scaleList.length)
            console.log('[scale-form:stage4] setData 前前3条:', scaleList.slice(0, 3))

            // 找到映射后的不育症诊断量表
            const testMappedScale = scaleList.find((scale: any) => scale.questionnaireName.includes('不育症诊断量表'))
            console.log('[step 4] scaleList 映射后 - 不育症诊断量表:', {
              questionnaireName: testMappedScale && testMappedScale.questionnaireName,
              templateId: testMappedScale && testMappedScale.templateId,
              id: testMappedScale && testMappedScale.id,
              scale: testMappedScale
            })

            console.log('[scale-form:debug] scales.length', scales.length)
            console.log('[scale-form:debug] uniqueScales.length', uniqueScales.length)
            console.log('[scale-form:debug] first scale raw', uniqueScales[0])
            console.log('[scale-form:debug] first scale processed', scaleList[0])
            console.log('[scale-form:debug] typeof first scale id', typeof (scaleList[0] && scaleList[0].id))

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
              isLoading: false,
              debugLastAction: 'loadScaleOptions:success'
            }

            console.log('[step 5] setData 前 - 不育症诊断量表:', {
              questionnaireName: testMappedScale && testMappedScale.questionnaireName,
              templateId: testMappedScale && testMappedScale.templateId,
              id: testMappedScale && testMappedScale.id,
              scale: testMappedScale
            })

            console.log('[scale-form:request-success] next state patch', patchObject)

            this.setData(patchObject, () => {
              // 找到 setData 后的不育症诊断量表
              const testSetDataScale = this.data.scaleList.find((scale: any) => scale.questionnaireName.includes('不育症诊断量表'))
              const testVisibleScale = this.data.visibleScales.find((scale: any) => scale.questionnaireName.includes('不育症诊断量表'))
              console.log('[step 6] setData 后 scaleList - 不育症诊断量表:', {
                questionnaireName: testSetDataScale && testSetDataScale.questionnaireName,
                templateId: testSetDataScale && testSetDataScale.templateId,
                id: testSetDataScale && testSetDataScale.id,
                scale: testSetDataScale
              })
              console.log('[step 6] setData 后 visibleScales - 不育症诊断量表:', {
                questionnaireName: testVisibleScale && testVisibleScale.questionnaireName,
                templateId: testVisibleScale && testVisibleScale.templateId,
                id: testVisibleScale && testVisibleScale.id,
                scale: testVisibleScale
              })

              console.log('[scale-form:setData-done] data snapshot', getScaleFormDebugSnapshot(this.data as Record<string, any>))
              logScaleFormRenderSource(this.data as Record<string, any>)
            })

            return
          }

          this.setData({
            isLoading: false,
            debugLastAction: `loadScaleOptions:non-200:${res.statusCode}`
          })
          wx.showToast({
            title: '加载量表数据失败',
            icon: 'none'
          })
        },
        fail: () => {
          this.setData({
            isLoading: false,
            debugLastAction: 'loadScaleOptions:fail'
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

      // 打印event.currentTarget.dataset
      console.log('[start] dataset=', event.currentTarget.dataset)
      
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
      
      // 打印日志
      console.log('[start] payload=', payload)
      console.log('[start] typeof templateId', typeof templateId)

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

        // 打印响应日志
        console.log('start questionnaire response', response)
        console.log('start questionnaire response data', response.data)

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
            console.log('before navigate current pages', getCurrentPages().map(p => p.route))
            console.log('navigate url', url)
            wx.navigateTo({
              url,
              success: (res) => {
                console.log('navigateTo success', res)
                console.log('after navigate current pages', getCurrentPages().map(p => p.route))
              },
              fail: (err) => {
                console.error('navigateTo fail', err)
                wx.showToast({
                  title: '页面跳转失败',
                  icon: 'none'
                })
              },
              complete: (res) => {
                console.log('navigateTo complete', res)
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
