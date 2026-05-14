const API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'

type DoctorOption = {
  id: string
  name: string
  department: string
  tags: string[]
}

type GenderOption = 'male' | 'female'

type ScaleItem = {
  id: string
  templateId: string
  questionnaireId: string
  questionnaireName: string
  description: string
  visitStage: string
  sourceBindingId: string
  required: boolean
}

type DiseaseOption = {
  value: string
  label: string
  description: string
  keywords: string[]
}

type VisitType = 'first' | 'followup' | 'referral'

const DISEASE_OPTIONS: DiseaseOption[] = [
  {
    value: 'male_infertility',
    label: '未孕',
    description: '适用于精液、生殖系统异常、未避孕一年等情况',
    keywords: ['不育', '男性不育', '精液', '生殖系统', '未孕']
  },
  {
    value: 'male_sexual_function',
    label: '(男科)不育症',
    description: '精液 / 生殖系统异常，未避孕一年',
    keywords: ['不育症', '男性不育', '不育病史', '不育诊断', '精液']
  },
  {
    value: 'male_sexual_dysfunction',
    label: '男性性功能障碍',
    description: '勃起 / 射精异常、性欲减退',
    keywords: ['性功能障碍', '勃起', '射精', '性欲']
  },
  {
    value: 'prostatitis',
    label: '前列腺炎',
    description: '尿频尿痛、会阴腰骶不适、滴白',
    keywords: ['前列腺炎', '前列腺', 'NIH-CPSI', 'I-PSS']
  },
  {
    value: 'premature_ejaculation',
    label: '早泄',
    description: '早泄相关评估量表',
    keywords: ['早泄', 'PEDT']
  },
  {
    value: 'other_male',
    label: '其他症状',
    description: '未归类的男科症状和一般问诊',
    keywords: ['问诊', '病史', '症状', '男性']
  },
  {
    value: 'female_infertility',
    label: '(妇科)不孕',
    description: '不孕、备孕困难、受孕相关评估',
    keywords: ['不孕', '妇科不孕', '不孕症', 'PCOS']
  },
  {
    value: 'menstrual_disorder',
    label: '月经不调',
    description: '周期、经量、经色、经质异常',
    keywords: ['月经不调', '月经', '经量', '周期']
  },
  {
    value: 'other_female',
    label: '其他',
    description: '未归类的妇科症状和一般问诊',
    keywords: ['妇科', '病史', '症状']
  },
  {
    value: 'tcm_gyn',
    label: '中医妇科预问诊',
    description: '初次就诊不明确病症请选这里',
    keywords: ['中医妇科预问诊']
  },
  {
    value: 'tcm_constitution',
    label: '中医体质辨识',
    description: '中医体质评估',
    keywords: ['中医体质辨识']
  }
]

const VISIT_TYPE_OPTIONS: Array<{ value: VisitType; label: string; description: string }> = [
  { value: 'first', label: '初诊', description: '首次就诊或首次建档' },
  { value: 'followup', label: '复诊', description: '持续随访或复查' },
  { value: 'referral', label: '转诊', description: '由其他机构转入' }
]

function normalizeText(value: unknown): string {
  return String(value || '').trim().toLowerCase()
}

function includesAny(text: string, keywords: string[]): boolean {
  return keywords.some((keyword) => text.includes(normalizeText(keyword)))
}

function getDiseaseOptionsForDoctor(_doctorName: string): DiseaseOption[] {
  return DISEASE_OPTIONS
}

function getAvailableDiseaseOptions(scales: ScaleItem[], doctorName: string): DiseaseOption[] {
  const baseOptions = getDiseaseOptionsForDoctor(doctorName)
  if (!scales.length) {
    return []
  }

  return baseOptions.filter((option) => {
    return scales.some((scale) => matchesDisease(scale.questionnaireName, option.value))
  })
}

function matchesDisease(questionnaireName: string, diseaseValue: string): boolean {
  const text = normalizeText(questionnaireName)
  const option = DISEASE_OPTIONS.find((item) => item.value === diseaseValue)
  if (!option) {
    return true
  }

  if (option.value === 'other_male' || option.value === 'other_female') {
    const blockedKeywords = DISEASE_OPTIONS
      .filter((item) => item.value !== option.value && !item.value.startsWith('other_'))
      .flatMap((item) => item.keywords.map((keyword) => normalizeText(keyword)))
    return !blockedKeywords.some((keyword) => keyword && text.includes(keyword))
  }

  return includesAny(text, option.keywords.map(normalizeText))
}

function matchesVisitStage(visitStage: string, selectedVisitType: string): boolean {
  if (selectedVisitType === 'first') {
    return true
  }

  return visitStage !== 'first_only'
}

function buildDiseaseText(option: DiseaseOption | null): string {
  if (!option) {
    return ''
  }

  return option.description ? `${option.label}\n${option.description}` : option.label
}

function getCurrentUserId(): number | null {
  const app = getApp<IAppOption>()
  const globalUserId = app?.globalData?.userId
  const storageUserId = wx.getStorageSync('USER_ID')
  const rawUserId = globalUserId || storageUserId
  const parsedUserId = Number(rawUserId)
  return Number.isFinite(parsedUserId) && parsedUserId > 0 ? parsedUserId : null
}

function getCurrentPageOptions(): Record<string, any> {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  return currentPage?.options || {}
}

function toDoctorOption(item: any): DoctorOption {
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
}

function toScaleItem(item: any): ScaleItem {
  const questionnaireId = String(item.questionnaireId || item.id || '')
  const visitStage = String(item.visitStage || '')

  return {
    id: String(item.bindId || item.id || questionnaireId),
    templateId: questionnaireId,
    questionnaireId,
    questionnaireName: String(item.questionnaireName || ''),
    description: visitStage === 'first_only' ? '首次就诊' : '常规',
    visitStage,
    sourceBindingId: String(item.sourceBindingId || ''),
    required: visitStage === 'first_only'
  }
}

Component({
  data: {
    doctorOptions: [] as DoctorOption[],
    doctorPickerRange: [] as string[],
    doctorPickerIndex: 0,
    selectedDoctor: null as DoctorOption | null,
    selectedDoctorText: '' as string,
    diseaseOptions: [] as DiseaseOption[],
    diseasePickerRange: [] as string[],
    diseasePickerIndex: 0,
    selectedDisease: null as DiseaseOption | null,
    selectedDiseaseText: '' as string,
    visitTypeOptions: VISIT_TYPE_OPTIONS,
    visitTypePickerRange: VISIT_TYPE_OPTIONS.map((item) => item.label),
    visitTypePickerIndex: 0,
    selectedVisitType: null as { value: VisitType; label: string; description: string } | null,
    selectedVisitTypeText: '' as string,
    allScaleList: [] as ScaleItem[],
    scaleList: [] as ScaleItem[],
    genderOptions: [
      { value: 'male', label: '男' },
      { value: 'female', label: '女' }
    ] as Array<{ value: GenderOption; label: string }>,
    selectedGender: null as GenderOption | null,
    canShowScales: false,
    visibleScales: [] as ScaleItem[],
    isLoading: false,
    patientId: '',
    doctorId: '',
    doctorName: '',
    isFirstVisit: false,
    pendingDoctorId: '',
    questionnaireVisitType: '',
    questionnaireDiseaseType: ''
  },
  lifetimes: {
    attached() {
      this.initializePage()
    }
  },
  pageLifetimes: {
    show() {
      if (this.data.selectedDoctor) {
        void this.loadScaleOptions()
      }
    }
  },
  methods: {
    initializePage() {
      const query = getCurrentPageOptions()
      const pendingDoctorId = String(query.doctorId || query.doctor_id || '').trim()
      const pendingDoctorName = String(query.doctorName || query.doctor_name || '').trim()
      const patientId = getCurrentUserId()

      this.setData({
        patientId: patientId ? String(patientId) : '',
        pendingDoctorId
      })

      void this.loadDoctorOptions(pendingDoctorId, pendingDoctorName)
    },

    async loadDoctorOptions(pendingDoctorId = '', pendingDoctorName = '') {
      this.setData({ isLoading: true })

      try {
        const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
          wx.request({
            url: `${API_BASE_URL}/api/doctors/list`,
            method: 'GET',
            success: resolve,
            fail: reject
          })
        })

        if (response.statusCode !== 200 || !response.data) {
          throw new Error('Failed to load doctors')
        }

        const responseData = response.data as any
        const doctors = Array.isArray(responseData?.data) ? responseData.data.map(toDoctorOption) : []

        this.setData({
          doctorOptions: doctors,
          doctorPickerRange: doctors.map((doctor) => `${doctor.name} ${doctor.department ? '· ' + doctor.department : ''}`),
          isLoading: false
        })

        if (pendingDoctorId) {
          const matchedDoctor = doctors.find((doctor) => doctor.id === pendingDoctorId)
          if (matchedDoctor) {
            this.selectDoctor(matchedDoctor)
            return
          }
        }

        if (pendingDoctorName) {
          const matchedDoctor = doctors.find((doctor) => doctor.name === pendingDoctorName)
          if (matchedDoctor) {
            this.selectDoctor(matchedDoctor)
          }
        }
      } catch (error) {
        this.setData({ isLoading: false })
        wx.showToast({
          title: 'Failed to load doctors',
          icon: 'none'
        })
      }
    },

    selectDoctor(doctor: DoctorOption) {
      this.setData({
        selectedDoctor: doctor,
        doctorId: doctor.id,
        doctorName: doctor.name,
        canShowScales: false,
        visibleScales: [],
        diseaseOptions: [],
        diseasePickerRange: [],
        diseasePickerIndex: 0,
        selectedDisease: null,
        selectedDiseaseText: '',
        visitTypeOptions: VISIT_TYPE_OPTIONS,
        visitTypePickerRange: VISIT_TYPE_OPTIONS.map((item) => item.label),
        visitTypePickerIndex: 0,
        selectedVisitType: null,
        selectedVisitTypeText: '',
        scaleList: [],
        allScaleList: [],
        isFirstVisit: false,
        questionnaireDiseaseType: '',
        questionnaireVisitType: ''
      })

      void this.loadScaleOptions()
    },

    async loadScaleOptions() {
      const selectedDoctor = this.data.selectedDoctor
      const patientId = getCurrentUserId()

      if (!selectedDoctor) {
        this.setData({
          canShowScales: false,
          visibleScales: [],
          scaleList: [],
          allScaleList: [],
          isLoading: false
        })
        return
      }

      if (!patientId) {
        wx.showToast({
          title: 'Please login first',
          icon: 'none'
        })
        return
      }

      this.setData({
        isLoading: true,
        patientId: String(patientId),
        doctorId: selectedDoctor.id,
        doctorName: selectedDoctor.name
      })

      try {
        const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
          wx.request({
            url: `${API_BASE_URL}/api/questionnaires/by-doctor`,
            method: 'GET',
            data: {
              doctorId: selectedDoctor.id,
              patientId
            },
            success: resolve,
            fail: reject
          })
        })

        if (response.statusCode !== 200 || !response.data) {
          throw new Error('Failed to load questionnaires')
        }

        const responseData = response.data as any
        const questionnaires = Array.isArray(responseData?.questionnaires) ? responseData.questionnaires : []
        const visibleScales = questionnaires.map(toScaleItem)

        this.setData({
          doctorId: String(responseData.doctorId || selectedDoctor.id),
          doctorName: String(responseData.doctorName || selectedDoctor.name),
          isFirstVisit: Boolean(responseData.isFirstVisit),
          allScaleList: visibleScales,
          scaleList: visibleScales,
          visibleScales,
          canShowScales: true,
          isLoading: false
        })
        this.syncDiseaseOptions()
        this.refreshVisibleScales()
      } catch (error) {
        this.setData({ isLoading: false })
        wx.showToast({
          title: 'Failed to load questionnaires',
          icon: 'none'
        })
      }
    },

    onDoctorPickerChange(event: WechatMiniprogram.CustomEvent) {
      console.log('[doctor-select] scale form doctor picker changed')
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
        selectedDoctorText
      })
      this.selectDoctor(selectedDoctor)
    },

    onSelectDoctor(event: WechatMiniprogram.CustomEvent) {
      const index = Number(event.currentTarget.dataset.index)
      if (Number.isNaN(index)) {
        return
      }

      const selectedDoctor = this.data.doctorOptions[index] || null
      if (!selectedDoctor) {
        return
      }

      this.selectDoctor(selectedDoctor)
    },

    onDiseasePickerChange(event: WechatMiniprogram.CustomEvent) {
      const index = Number(event.detail?.value ?? -1)
      if (Number.isNaN(index) || index < 0 || index >= this.data.diseaseOptions.length) {
        return
      }

      const selectedDisease = this.data.diseaseOptions[index]
      this.setData({
        diseasePickerIndex: index,
        selectedDisease,
        selectedDiseaseText: `${selectedDisease.label}${selectedDisease.description ? ` · ${selectedDisease.description}` : ''}`,
        questionnaireDiseaseType: selectedDisease.value
      })
      this.refreshVisibleScales()
    },

    onVisitTypePickerChange(event: WechatMiniprogram.CustomEvent) {
      const index = Number(event.detail?.value ?? -1)
      if (Number.isNaN(index) || index < 0 || index >= this.data.visitTypeOptions.length) {
        return
      }

      const selectedVisitType = this.data.visitTypeOptions[index]
      this.setData({
        visitTypePickerIndex: index,
        selectedVisitType,
        selectedVisitTypeText: selectedVisitType.label,
        questionnaireVisitType: selectedVisitType.value
      })
      this.refreshVisibleScales()
    },

    syncDiseaseOptions() {
      const { allScaleList, selectedDoctor, selectedDisease } = this.data
      const doctorName = selectedDoctor?.name || ''
      const availableDiseaseOptions = getAvailableDiseaseOptions(allScaleList, doctorName)
      const selectedDiseaseValue = selectedDisease?.value || ''
      const currentDiseaseStillAvailable = availableDiseaseOptions.some((item) => item.value === selectedDiseaseValue)

      this.setData({
        diseaseOptions: availableDiseaseOptions,
        diseasePickerRange: availableDiseaseOptions.map((item) => item.label),
        diseasePickerIndex: currentDiseaseStillAvailable
          ? availableDiseaseOptions.findIndex((item) => item.value === selectedDiseaseValue)
          : 0,
        selectedDisease: currentDiseaseStillAvailable ? selectedDisease : null,
        selectedDiseaseText: currentDiseaseStillAvailable ? buildDiseaseText(selectedDisease) : '',
        questionnaireDiseaseType: currentDiseaseStillAvailable ? selectedDiseaseValue : ''
      })
    },

    refreshVisibleScales() {
      const { allScaleList, selectedDisease, selectedVisitType } = this.data
      const diseaseValue = selectedDisease?.value || ''
      const visitTypeValue = selectedVisitType?.value || ''

      let filteredList = allScaleList.slice()
      if (!diseaseValue || !visitTypeValue) {
        this.setData({
          scaleList: [],
          visibleScales: [],
          canShowScales: false
        })
        return
      }

      if (diseaseValue) {
        filteredList = filteredList.filter((item) => matchesDisease(item.questionnaireName, diseaseValue))
      }

      filteredList = filteredList.filter((item) => matchesVisitStage(item.visitStage, visitTypeValue))

      this.setData({
        scaleList: filteredList,
        visibleScales: filteredList,
        canShowScales: Boolean(this.data.selectedDoctor && diseaseValue && selectedVisitType)
      })
    },

    onSelectGender(event: WechatMiniprogram.CustomEvent) {
      const selectedGender = event.currentTarget.dataset.value as GenderOption
      if (!selectedGender) {
        return
      }
      this.setData({ selectedGender })
    },

    validateBeforeStart() {
      if (!this.data.selectedDoctor) {
        return 'Please select a doctor'
      }

      if (!this.data.selectedDisease) {
        return 'Please select a disease type'
      }

      if (!this.data.selectedVisitType) {
        return 'Please select a visit type'
      }

      const patientId = getCurrentUserId()
      if (!patientId) {
        return 'Please login first'
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

      const questionnaireId = String(
        event.currentTarget.dataset.questionnaireId ||
        event.currentTarget.dataset.templateId ||
        event.currentTarget.dataset.id ||
        ''
      )
      const questionnaireName = String(event.currentTarget.dataset.name || '')

      if (!questionnaireId) {
        wx.showToast({
          title: 'Invalid questionnaire ID',
          icon: 'none'
        })
        return
      }

      console.log('[scale-form] start item.questionnaireId =', questionnaireId)

      const patientId = getCurrentUserId()
      const selectedDoctor = this.data.selectedDoctor
      const doctorId = selectedDoctor ? String(selectedDoctor.id) : ''
      const selectedDisease = this.data.selectedDisease
      const selectedVisitType = this.data.selectedVisitType

      if (!patientId || !doctorId) {
        wx.showToast({
          title: 'Please select a doctor and login',
          icon: 'none'
        })
        return
      }

      const payload = {
        externalUserId: String(patientId),
        patientId: String(patientId),
        doctorId: String(doctorId),
        questionnaireId: questionnaireId,
        templateId: questionnaireId,
        diseaseType: selectedDisease ? selectedDisease.value : '',
        visitType: selectedVisitType ? selectedVisitType.value : ''
      }

      try {
        const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
          wx.request({
            url: `${API_BASE_URL}/api/questionnaires/start`,
            method: 'POST',
            header: {
              'Content-Type': 'application/json'
            },
            data: payload,
            success: resolve,
            fail: reject
          })
        })

        if (response.statusCode === 200 && response.data) {
          const data = response.data as { recordId?: string }
          const recordId = String(data.recordId || '')

          if (!recordId) {
            wx.showToast({
              title: 'Failed to get record ID',
              icon: 'none'
            })
            return
          }

          wx.showToast({
            title: `Start: ${questionnaireName || 'questionnaire'}`,
            icon: 'success'
          })

          wx.navigateTo({
            url: `/pages/questionnaire/questionnaire?recordId=${recordId}&doctorId=${doctorId}&patientId=${patientId}&questionnaireId=${encodeURIComponent(questionnaireId)}&doctorName=${encodeURIComponent(selectedDoctor?.name || '')}&diseaseType=${encodeURIComponent(selectedDisease?.value || '')}&visitType=${encodeURIComponent(selectedVisitType?.value || '')}&diseaseName=${encodeURIComponent(selectedDisease?.label || '')}&visitTypeLabel=${encodeURIComponent(selectedVisitType?.label || '')}`,
            fail: () => {
              wx.showToast({
                title: 'Page navigation failed',
                icon: 'none'
              })
            }
          })
        } else {
          wx.showToast({
            title: 'Failed to start questionnaire',
            icon: 'none'
          })
        }
      } catch (error) {
        wx.showToast({
          title: 'Network error, please try again',
          icon: 'none'
        })
      }
    }
  }
})
