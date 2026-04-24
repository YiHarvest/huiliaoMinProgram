import { handleSubscribeAuthorization } from '../../utils/subscribe'

const TONGUE_API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'
const MAX_VIDEO_SIZE = 5 * 1024 * 1024
const MIN_VIDEO_DURATION = 10
const MAX_VIDEO_DURATION = 20
const MIN_VIDEO_FPS = 2

type ImageField = 'topImage' | 'bottomImage' | 'faceImage'
type MediaField = ImageField | 'tongueVideo'

type ImageEntry = {
  url: string
  name: string
}

type VideoEntry = {
  url: string
  thumbUrl: string
  name: string
  size: number
  sizeLabel: string
  duration: number
  fps: number
  durationLabel: string
  fpsLabel: string
}

type DescriptionItem = {
  description: string
  manifestations?: string[] | null
}

type DietSuggestion = {
  name: string
  effect: string
}

type AnalysisReport = {
  analysisId: string
  overall: {
    subject: string
    score?: number
    summary: string
    riskWarnings: string[]
  }
  healthSuggestions: {
    diet: DietSuggestion[]
    exercise: string
    physicalTherapy: string
  }
  tongueAnalysis: {
    summary: string
    tongueColor: DescriptionItem[]
    tongueShape: DescriptionItem[]
    coatingTexture: DescriptionItem[]
    coatingColor: DescriptionItem[]
  }
  faceAnalysis: {
    summary: string
    complexion: DescriptionItem[]
    nose: DescriptionItem[]
    shape: DescriptionItem[]
    yinTang: DescriptionItem[]
    lipColor: DescriptionItem[]
    eyeState: DescriptionItem[]
  }
  healthAnalysis: {
    subjectName: string
    subjectFeature: string
    subjectOutline: string
    dietAccept: string
    dietReject: string
    exerciseAccept: string
    exerciseReject: string
    physicalPosition: string
    physicalSearch: string
    physicalOperation: string
  }
  basicInfo: {
    sex: string
    age: string | number
  }
}

type UploadResponse = {
  report?: AnalysisReport
  tips?: string | null
  error?: string
  errorCode?: string
}

type ReportView = {
  tongueColor: string[]
  tongueShape: string[]
  coatingTexture: string[]
  coatingColor: string[]
  complexion: string[]
  nose: string[]
  shape: string[]
  yinTang: string[]
  lipColor: string[]
  eyeState: string[]
}

function getFileName(filePath: string) {
  return filePath.split('/').pop() || filePath.split('\\').pop() || '本地文件'
}

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size}B`
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)}KB`
  }

  return `${(size / (1024 * 1024)).toFixed(1)}MB`
}

function canSubmitWithState(data: Record<string, any>) {
  return Boolean(data.tongueVideo && !data.isSubmitting)
}

function validateVideoEntry(video: VideoEntry | null) {
  if (!video) {
    return '请上传舌苔视频'
  }

  if (video.size > MAX_VIDEO_SIZE) {
    return '视频大小不能超过 5MB'
  }

  if (video.duration > 0 && (video.duration <= MIN_VIDEO_DURATION || video.duration >= MAX_VIDEO_DURATION)) {
    return '视频时长需大于 10 秒且小于 20 秒'
  }

  if (video.fps > 0 && video.fps <= MIN_VIDEO_FPS) {
    return '视频帧率需大于 2fps'
  }

  return ''
}

function uploadTongueVideo(filePath: string): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${TONGUE_API_BASE_URL}/api/tongue-analysis`,
      filePath,
      name: 'video',
      timeout: 120000,
      success: res => {
        let data: UploadResponse
        try {
          data = JSON.parse(res.data) as UploadResponse
        } catch (error) {
          reject(new Error('分析结果解析失败'))
          return
        }

        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(data.error || '上传分析失败'))
          return
        }

        if (!data.report) {
          reject(new Error(data.error || '未返回分析报告'))
          return
        }

        resolve(data)
      },
      fail: error => {
        reject(new Error(error.errMsg || '分析请求失败'))
      }
    })
  })
}

function toSectionItems(items: DescriptionItem[]) {
  return items.map(item => item.description).filter(Boolean)
}

function buildReportView(report: AnalysisReport): ReportView {
  return {
    tongueColor: toSectionItems(report.tongueAnalysis.tongueColor || []),
    tongueShape: toSectionItems(report.tongueAnalysis.tongueShape || []),
    coatingTexture: toSectionItems(report.tongueAnalysis.coatingTexture || []),
    coatingColor: toSectionItems(report.tongueAnalysis.coatingColor || []),
    complexion: toSectionItems(report.faceAnalysis.complexion || []),
    nose: toSectionItems(report.faceAnalysis.nose || []),
    shape: toSectionItems(report.faceAnalysis.shape || []),
    yinTang: toSectionItems(report.faceAnalysis.yinTang || []),
    lipColor: toSectionItems(report.faceAnalysis.lipColor || []),
    eyeState: toSectionItems(report.faceAnalysis.eyeState || [])
  }
}

function emptyReportView(): ReportView {
  return {
    tongueColor: [],
    tongueShape: [],
    coatingTexture: [],
    coatingColor: [],
    complexion: [],
    nose: [],
    shape: [],
    yinTang: [],
    lipColor: [],
    eyeState: []
  }
}

Component({
  data: {
    tongueVideo: null as VideoEntry | null,
    topImage: null as ImageEntry | null,
    bottomImage: null as ImageEntry | null,
    faceImage: null as ImageEntry | null,
    canSubmit: false,
    isSubmitting: false,
    hasReport: false,
    report: null as AnalysisReport | null,
    reportView: emptyReportView(),
    tipsText: '',
    progressText: '',
    reportScrollId: '',
    videoLimitText: '大小不能超过 5M，时长大于 10 秒且小于 20 秒，帧率大于 2fps。',
    exampleAssets: {
      topImage: '/assets/tongue-top-example.png',
      bottomImage: '/assets/tongue-bottom-example.png',
      tongueVideo: '/assets/tongue-video-example.png',
      faceImage: '/assets/face-example.png'
    },
    exampleVideoUrl: `${TONGUE_API_BASE_URL}/examples/tongue-video`,
    shootingRequirements: [
      '自然光照下拍摄，避免使用闪光灯',
      '舌头自然伸出，放松不要用力',
      '拍摄前不要吃有色食物或饮料',
      '确保图片清晰，不要模糊或过曝'
    ],
    openid: ''
  },
  methods: {
    onChooseImage(event: WechatMiniprogram.CustomEvent) {
      const field = event.currentTarget.dataset.field as ImageField

      wx.chooseMedia({
        count: 1,
        mediaType: ['image'],
        sourceType: ['album', 'camera'],
        sizeType: ['compressed'],
        success: res => {
          const file = res.tempFiles[0]

          if (!file) {
            return
          }

          const nextValue: ImageEntry = {
            url: file.tempFilePath,
            name: getFileName(file.tempFilePath)
          }

          this.setData({
            [field]: nextValue
          })
        }
      })
    },
    onChooseVideo() {
      wx.chooseMedia({
        count: 1,
        mediaType: ['video'],
        sourceType: ['album', 'camera'],
        maxDuration: 20,
        camera: 'front',
        success: res => {
          const file = res.tempFiles[0] as WechatMiniprogram.MediaFile & {
            thumbTempFilePath?: string
          }

          if (!file) {
            return
          }

          wx.getVideoInfo({
            src: file.tempFilePath,
            success: info => {
              const nextVideo: VideoEntry = {
                url: file.tempFilePath,
                thumbUrl: file.thumbTempFilePath || '/assets/tongue-video-example.png',
                name: getFileName(file.tempFilePath),
                size: file.size,
                sizeLabel: formatFileSize(file.size),
                duration: info.duration,
                fps: info.fps || 0,
                durationLabel: `${info.duration.toFixed(1)}秒`,
                fpsLabel: info.fps ? `${info.fps}fps` : '未知'
              }

              const validationMessage = validateVideoEntry(nextVideo)
              if (validationMessage) {
                wx.showToast({
                  title: validationMessage,
                  icon: 'none'
                })
                return
              }

              this.setData({
                tongueVideo: nextVideo,
                hasReport: false,
                report: null,
                reportView: emptyReportView(),
                tipsText: '',
                canSubmit: canSubmitWithState({
                  ...this.data,
                  tongueVideo: nextVideo,
                  isSubmitting: false
                })
              })
            },
            fail: () => {
              if (file.size > MAX_VIDEO_SIZE) {
                wx.showToast({
                  title: '视频大小不能超过 5MB',
                  icon: 'none'
                })
                return
              }

              const nextVideo: VideoEntry = {
                url: file.tempFilePath,
                thumbUrl: file.thumbTempFilePath || '/assets/tongue-video-example.png',
                name: getFileName(file.tempFilePath),
                size: file.size,
                sizeLabel: formatFileSize(file.size),
                duration: 0,
                fps: 0,
                durationLabel: '未知',
                fpsLabel: '未知'
              }

              this.setData({
                tongueVideo: nextVideo,
                hasReport: false,
                report: null,
                reportView: emptyReportView(),
                tipsText: '视频信息读取失败，将基于文件大小进行初步校验',
                canSubmit: canSubmitWithState({
                  ...this.data,
                  tongueVideo: nextVideo,
                  isSubmitting: false
                })
              })
            }
          })
        }
      })
    },
    onPreviewImage(event: WechatMiniprogram.CustomEvent) {
      const url = event.currentTarget.dataset.url as string

      if (!url) {
        return
      }

      wx.previewImage({
        urls: [url],
        current: url
      })
    },
    previewVideoByUrl(url: string, poster?: string) {
      const previewMedia = (wx as WechatMiniprogram.Wx & {
        previewMedia?: (options: {
          sources: Array<{ url: string; type: 'video'; poster?: string }>
        }) => void
      }).previewMedia

      if (!previewMedia) {
        wx.showModal({
          title: '视频地址',
          content: url,
          showCancel: false
        })
        return
      }

      previewMedia({
        sources: [
          {
            url,
            type: 'video',
            poster
          }
        ]
      })
    },
    onPreviewVideo() {
      const video = this.data.tongueVideo

      if (!video) {
        return
      }

      this.previewVideoByUrl(video.url, video.thumbUrl)
    },
    onPreviewExampleVideo() {
      this.previewVideoByUrl(this.data.exampleVideoUrl, this.data.exampleAssets.tongueVideo)
    },
    onRemoveMedia(event: WechatMiniprogram.CustomEvent) {
      const field = event.currentTarget.dataset.field as MediaField
      const nextState = {
        ...this.data,
        [field]: null
      }

      this.setData({
        [field]: null,
        canSubmit: canSubmitWithState(nextState)
      })
    },
    onRechooseImage(event: WechatMiniprogram.CustomEvent) {
      this.onChooseImage(event)
    },
    onRechooseVideo() {
      this.onChooseVideo()
    },
    validateForm() {
      return validateVideoEntry(this.data.tongueVideo)
    },
    async onSubmit() {
      const validationMessage = this.validateForm()

      if (validationMessage) {
        wx.showToast({
          title: validationMessage,
          icon: 'none'
        })
        return
      }

      const tongueVideo = this.data.tongueVideo
      if (!tongueVideo) {
        return
      }

      this.setData({
        isSubmitting: true,
        canSubmit: false,
        progressText: '正在上传并分析，请稍候…'
      })
      wx.showLoading({
        title: '分析中',
        mask: true
      })

      try {
        const response = await uploadTongueVideo(tongueVideo.url)
        const report = response.report as AnalysisReport
        this.setData({
          report,
          reportView: buildReportView(report),
          hasReport: true,
          tipsText: response.tips || '',
          reportScrollId: 'analysis-report'
        })
        wx.hideLoading()
        if (response.tips) {
          wx.showModal({
            title: '分析提示',
            content: response.tips,
            showCancel: false
          })
        }
        wx.showToast({
          title: '分析完成',
          icon: 'success'
        })
      } catch (error) {
        wx.hideLoading()
        wx.showToast({
          title: error instanceof Error ? error.message : '分析失败，请稍后重试',
          icon: 'none'
        })
      } finally {
        this.setData({
          isSubmitting: false,
          progressText: '',
          canSubmit: canSubmitWithState({
            ...this.data,
            isSubmitting: false
          })
        })
      }
    },
    async onSubscribeReminder() {
      const openid = this.data.openid
      
      if (!openid) {
        wx.showModal({
          title: '提示',
          content: '请先登录后再开启消息提醒',
          showCancel: false
        })
        return
      }

      await handleSubscribeAuthorization(openid, ['tongue_result'])
    }
  }
})