import { expertProfiles } from '../../data/experts'

type DoctorOption = {
  id: string
  name: string
  department: string
  tags: string[]
}

type GenderOption = 'male' | 'female'

type SymptomOption = '失眠' | '焦虑' | '抑郁' | '慢性疼痛' | '健康管理' | '其他'

type ScaleItem = {
  id: string
  name: string
  summary: string
  symptoms: SymptomOption[]
}

const doctorOptions: DoctorOption[] = expertProfiles.slice(0, 4).map((expert) => ({
  id: expert.id,
  name: expert.name,
  department: expert.department,
  tags: expert.focus.slice(0, 2)
}))

const symptomOptions: SymptomOption[] = ['失眠', '焦虑', '抑郁', '慢性疼痛', '健康管理', '其他']

const scaleCatalog: ScaleItem[] = [
  {
    id: 'psqi',
    name: 'PSQI 睡眠质量量表',
    summary: '用于评估近期睡眠质量与睡眠结构。',
    symptoms: ['失眠']
  },
  {
    id: 'gad7',
    name: 'GAD-7 焦虑量表',
    summary: '用于评估焦虑相关症状程度。',
    symptoms: ['焦虑']
  },
  {
    id: 'phq9',
    name: 'PHQ-9 抑郁量表',
    summary: '用于评估抑郁情绪与相关表现。',
    symptoms: ['抑郁']
  },
  {
    id: 'pain',
    name: '疼痛评估量表',
    summary: '用于记录疼痛部位、程度与持续情况。',
    symptoms: ['慢性疼痛']
  },
  {
    id: 'health',
    name: '健康管理基础量表',
    summary: '用于建立当前健康状态基础档案。',
    symptoms: ['健康管理', '其他']
  }
]

function getRecommendedScales(symptom: SymptomOption | null) {
  if (!symptom) {
    return scaleCatalog
  }

  const prioritized = scaleCatalog.filter((item) => item.symptoms.includes(symptom))
  const fallback = scaleCatalog.filter((item) => !item.symptoms.includes(symptom))
  return [...prioritized, ...fallback]
}

function buildStatePatch(data: {
  selectedDoctor: DoctorOption | null
  selectedGender: GenderOption | null
  selectedSymptom: SymptomOption | null
}) {
  const ready = Boolean(data.selectedDoctor && data.selectedGender && data.selectedSymptom)

  return {
    canShowScales: ready,
    visibleScales: ready ? getRecommendedScales(data.selectedSymptom) : []
  }
}

Component({
  data: {
    doctorOptions,
    symptomOptions,
    genderOptions: [
      { value: 'male', label: '男' },
      { value: 'female', label: '女' }
    ] as Array<{ value: GenderOption; label: string }>,
    selectedDoctor: null as DoctorOption | null,
    selectedGender: null as GenderOption | null,
    selectedSymptom: null as SymptomOption | null,
    canShowScales: false,
    visibleScales: [] as ScaleItem[]
  },
  methods: {
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
              selectedSymptom: this.data.selectedSymptom
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
          selectedSymptom: this.data.selectedSymptom
        })
      })
    },
    onChooseSymptom() {
      wx.showActionSheet({
        itemList: this.data.symptomOptions,
        success: (res) => {
          const selectedSymptom = this.data.symptomOptions[res.tapIndex] || null

          this.setData({
            selectedSymptom,
            ...buildStatePatch({
              selectedDoctor: this.data.selectedDoctor,
              selectedGender: this.data.selectedGender,
              selectedSymptom
            })
          })
        }
      })
    },
    validateBeforeStart() {
      if (!this.data.selectedDoctor) {
        return '请先确认医生信息'
      }

      if (!this.data.selectedGender) {
        return '请选择性别'
      }

      if (!this.data.selectedSymptom) {
        return '请选择疾病症状'
      }

      return ''
    },
    onStartScale(event: WechatMiniprogram.CustomEvent) {
      const validationMessage = this.validateBeforeStart()

      if (validationMessage) {
        wx.showToast({
          title: validationMessage,
          icon: 'none'
        })
        return
      }

      const name = event.currentTarget.dataset.name as string

      wx.showToast({
        title: `${name}待接入`,
        icon: 'none'
      })
    }
  }
})
