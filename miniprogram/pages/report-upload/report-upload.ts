import { expertProfiles } from '../../data/experts'

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

const doctorOptions: DoctorOption[] = expertProfiles.slice(0, 4).map((expert) => ({
  id: expert.id,
  name: expert.name,
  department: expert.department,
  tags: expert.focus.slice(0, 2)
}))

function getFileName(filePath: string) {
  return filePath.split('/').pop() || filePath.split('\\').pop() || '本地文件'
}

function canSubmitWithState(data: {
  selectedDoctor: DoctorOption | null
  reportImages: ReportImage[]
}) {
  return Boolean(data.selectedDoctor && data.reportImages.length > 0)
}

Component({
  data: {
    doctorOptions,
    selectedDoctor: null as DoctorOption | null,
    reportImages: [] as ReportImage[],
    maxReportImages: MAX_REPORT_IMAGES,
    canSubmit: false
  },
  methods: {
    onChooseDoctor() {
      wx.showActionSheet({
        itemList: this.data.doctorOptions.map((doctor) => `${doctor.name} · ${doctor.department}`),
        success: (res) => {
          const selectedDoctor = this.data.doctorOptions[res.tapIndex] || null

          this.setData({
            selectedDoctor,
            canSubmit: canSubmitWithState({
              selectedDoctor,
              reportImages: this.data.reportImages
            })
          })
        }
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
              reportImages
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
          reportImages
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

      wx.showToast({
        title: '报告已提交',
        icon: 'success'
      })
    }
  }
})
