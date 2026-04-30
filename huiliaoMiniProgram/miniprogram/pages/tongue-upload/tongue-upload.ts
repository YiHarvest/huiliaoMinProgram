import { handleSubscribeAuthorization } from '../../utils/subscribe'

const TONGUE_API_BASE_URL = 'https://miniprogram.huiliaoyiyuan.com'
const MAX_VIDEO_SIZE = 5 * 1024 * 1024
const MIN_VIDEO_DURATION = 10
const MAX_VIDEO_DURATION = 20
const MIN_RECORD_DURATION = 11
const MAX_RECORD_DURATION = 19
const MIN_VIDEO_FPS = 2

type ImageField = 'topImage' | 'bottomImage' | 'faceImage'
type MediaField = ImageField | 'tongueVideo'

interface ImageEntry {
  url: string
  name: string
}

interface VideoEntry {
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

interface DescriptionItem {
  description: string
  manifestations?: string[] | null
}

interface DietSuggestion {
  name: string
  effect: string
}

interface AnalysisReport {
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

interface UploadResponse {
  report?: AnalysisReport
  tips?: string | null
  error?: string
  errorCode?: string
}

interface ReportView {
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

interface FaceRect {
  x: number
  y: number
  width: number
  height: number
}

type ButtonState = 'idle' | 'recording' | 'analyzing' | 'completed' | 'failed'

function getFileName(filePath: string): string {
  return filePath.split('/').pop() || filePath.split('\\').pop() || '本地文件'
}

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size}B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)}KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)}MB`
}

function canSubmitWithState(data: Record<string, unknown>): boolean {
  return !!(data.tongueVideo && !data.isSubmitting)
}

function validateVideoEntry(video: VideoEntry | null): string {
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
      success: (res) => {
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
      fail: (error) => {
        reject(new Error(error.errMsg || '分析请求失败'))
      }
    })
  })
}

function toSectionItems(items: DescriptionItem[]): string[] {
  return items.map((item) => item.description).filter(Boolean)
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

const CameraStatus = {
  INIT: 'init',
  NO_PERMISSION: 'no_permission',
  NO_FACE: 'no_face',
  FACE_NOT_CENTERED: 'face_not_centered',
  FACE_CENTERED: 'face_centered',
  RECORDING: 'recording',
  ANALYZING: 'analyzing',
  FACE_DETECT_NOT_SUPPORTED: 'face_detect_not_supported',
  VIDEO_PARSE_FAILED: 'video_parse_failed'
} as const

type CameraStatusType = typeof CameraStatus[keyof typeof CameraStatus]

function getStatusTip(status: CameraStatusType): string {
  const tips: Record<CameraStatusType, string> = {
    init: '正在启动摄像头',
    no_permission: '请允许使用摄像头',
    no_face: '请正对摄像头，露出口鼻并伸出舌头',
    face_not_centered: '请将脸部移动到圆框中央',
    face_centered: '请张嘴伸舌后开始录制',
    recording: '录制中，请保持面部稳定',
    analyzing: '录制完成，正在上传分析',
    face_detect_not_supported: '请保持面部和舌部在圆框中央',
    video_parse_failed: '请重新录制视频'
  }
  return tips[status]
}

function getErrorMessage(errorCode?: string, errorMessage?: string): string {
  if (!errorCode && !errorMessage) {
    return '分析失败，请稍后重试'
  }
  const errorMap: Record<string, string> = {
    'VIDEO_POOR_QUALITY': '视频质量不符合要求，请重新录制 11-19 秒视频，并确保画面中有人脸和舌头。',
    'HEALTH_ANALYSIS_ERROR': '舌面检测分析失败，请稍后重试。',
    'FILE_TOO_LARGE': '视频大小超过5MB，请重新录制或压缩后上传。',
    'INVALID_DURATION': '视频需大于10秒且小于20秒，请重新录制。',
    'NETWORK_ERROR': '网络异常，请稍后重试。',
    'VIDEO_DURATION_ERROR': '视频时长异常，请重新录制。'
  }
  if (errorCode && errorMap[errorCode]) {
    return errorMap[errorCode]
  }
  return errorMessage || '分析失败，请稍后重试'
}

Page({
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
      '确保视频清晰，不要模糊或过曝'
    ],
    openid: '',

    showCameraMode: true,
    cameraStatus: 'init' as CameraStatusType,
    cameraTip: '正在启动摄像头',
    isRecording: false,
    recordDuration: 0,
    canRecord: false,
    faceRect: null as FaceRect | null,
    faceDetectSupported: true,
    frameCount: 0,
    detectInterval: 10,

    buttonState: 'idle' as ButtonState,
    canStopRecording: false,

    cameraContext: null as unknown,
    recordTimer: null as unknown,
    frameListener: null as unknown,
    recordStartTime: 0 as number,
    
    lightStatus: 'checking' as 'good' | 'dark' | 'overexposed' | 'checking' | 'unknown',
    lastLightCheckTime: 0 as number,
    lightTip: '检测中...',
    frameCount: 0 as number
  },

  lightTimeoutTimer: null as ReturnType<typeof setTimeout> | null,

  onCameraError(event: WechatMiniprogram.CameraError): void {
    console.error('Camera error:', event.detail)
    if (event.detail.errMsg.includes('permission')) {
      this.setCameraStatus('no_permission')
    } else {
      this.setCameraStatus('face_detect_not_supported')
    }
  },

  onCameraInitDone(): void {
    console.log('camera init done')
    const ctx = wx.createCameraContext()
    this.setData({
      cameraContext: ctx,
      canRecord: true,
      buttonState: 'idle' as ButtonState,
      lightStatus: 'checking',
      lightTip: '检测中...',
      frameCount: 0
    })
    this.checkFaceDetectSupport()
    
    const timer = setTimeout(() => {
      this.startFrameListener()
    }, 300)
    
    this.lightTimeoutTimer = setTimeout(() => {
      const frameCount = this.data.frameCount as number
      if (frameCount === 0) {
        console.log('Light detection timeout - no frames received')
        this.setData({
          lightStatus: 'unknown',
          lightTip: '光线检测不可用，请保持环境明亮'
        })
        this.stopFrameListener()
      }
    }, 3000)
  },

  checkFaceDetectSupport(): void {
    this.setData({
      faceDetectSupported: false
    })
    this.setCameraStatus('face_detect_not_supported')
  },

  startFrameListener(): void {
    console.log('startFrameListener called')
    
    const ctx = this.data.cameraContext as WechatMiniprogram.CameraContext | null
    if (!ctx) {
      console.log('cameraContext does not exist')
      return
    }
    
    console.log('cameraContext exists')
    console.log('Starting frame listener for light detection')
    
    this.stopFrameListener()
    
    let localFrameCount = 0
    let lastCheckTime = 0
    
    try {
      const frameListener = ctx.onCameraFrame((frame) => {
        console.log('camera frame received', frame.width, frame.height, frame.data.byteLength)
        localFrameCount++
        this.setData({ frameCount: localFrameCount })
        
        if (localFrameCount % 20 === 0) {
          console.log('camera frame received', frame.width, frame.height, frame.data.byteLength)
        }
        
        const now = Date.now()
        if (now - lastCheckTime < 500) {
          return
        }
        
        lastCheckTime = now
        this.setData({ lastLightCheckTime: now })
        this.analyzeLight(frame)
      })
      
      console.log('onCameraFrame listener created')
      
      this.setData({ frameListener })
      
      frameListener.start({
        success: () => {
          console.log('camera frame listener start success')
        },
        fail: (err) => {
          console.log('camera frame listener start fail', err)
          this.setData({
            lightStatus: 'unknown',
            lightTip: '请保持环境光线充足'
          })
        }
      })
    } catch (error) {
      console.error('onCameraFrame not supported or error:', error)
      this.setData({
        lightStatus: 'unknown',
        lightTip: '请保持环境光线充足'
      })
    }
  },

  analyzeLight(frame: WechatMiniprogram.CameraFrame): void {
    try {
      const data = frame.data
      const width = frame.width
      const height = frame.height
      
      if (!data || width === 0 || height === 0) {
        return
      }

      const sampleStep = 10
      let totalBrightness = 0
      let darkCount = 0
      let brightCount = 0
      let sampleCount = 0

      for (let y = 0; y < height; y += sampleStep) {
        for (let x = 0; x < width; x += sampleStep) {
          const index = (y * width + x) * 4
          if (index + 3 < data.length) {
            const r = data[index]
            const g = data[index + 1]
            const b = data[index + 2]
            
            const brightness = 0.299 * r + 0.587 * g + 0.114 * b
            totalBrightness += brightness
            sampleCount++
            
            if (brightness < 50) {
              darkCount++
            }
            if (brightness > 230) {
              brightCount++
            }
          }
        }
      }

      if (sampleCount === 0) {
        return
      }

      const averageBrightness = totalBrightness / sampleCount
      const darkRatio = darkCount / sampleCount
      const brightRatio = brightCount / sampleCount

      console.log(`Light analysis - avg: ${averageBrightness.toFixed(1)}, darkRatio: ${darkRatio.toFixed(2)}, brightRatio: ${brightRatio.toFixed(2)}`)

      let lightStatus: 'good' | 'dark' | 'overexposed' | 'checking' = 'good'
      let lightTip = '光线充足'
      
      if (averageBrightness < 70 || darkRatio > 0.45) {
        lightStatus = 'dark'
        lightTip = '光线偏暗，请靠近光源'
      } else if (averageBrightness > 220 || brightRatio > 0.35) {
        lightStatus = 'overexposed'
        lightTip = '光线过强，请避免强光直射'
      } else {
        lightStatus = 'good'
        lightTip = '光线充足'
      }

      this.setData({ lightStatus, lightTip })
    } catch (error) {
      console.error('Light analysis error:', error)
    }
  },

  stopFrameListener(): void {
    const listener = this.data.frameListener as { stop: () => void } | null
    if (listener) {
      try {
        listener.stop()
        this.setData({ frameListener: null })
        console.log('Frame listener stopped')
      } catch (error) {
        console.error('Failed to stop frame listener:', error)
      }
    }
    
    if (this.lightTimeoutTimer) {
      clearTimeout(this.lightTimeoutTimer)
      this.lightTimeoutTimer = null
    }
  },

  detectFace(): void {
  },

  setCameraStatus(status: CameraStatusType): void {
    this.setData({
      cameraStatus: status,
      cameraTip: getStatusTip(status)
    })
  },

  onToggleRecord(): void {
    const ctx = this.data.cameraContext as WechatMiniprogram.CameraContext | null
    if (!ctx) return

    if (this.data.isRecording) {
      if (this.data.recordDuration < MIN_RECORD_DURATION) {
        wx.showToast({
          title: `录制时长不足${MIN_RECORD_DURATION}秒，请继续录制`,
          icon: 'none',
          duration: 2000
        })
        return
      }
      this.stopRecording()
    } else {
      this.startRecording()
    }
  },

  startRecording(): void {
    const ctx = this.data.cameraContext as WechatMiniprogram.CameraContext | null
    if (!ctx) return

    if (this.data.isRecording) {
      console.log('正在录制中，请勿重复点击')
      return
    }

    if (this.data.isSubmitting) {
      console.log('正在上传分析中，请勿重复点击')
      return
    }

    console.log('startRecord 开始录制')

    this.setData({
      isRecording: true,
      recordDuration: 0,
      recordStartTime: Date.now(),
      cameraTip: '录制中，请保持面部稳定',
      canRecord: false,
      buttonState: 'recording' as ButtonState,
      canStopRecording: false
    })

    const timer = setInterval(() => {
      const currentDuration = this.data.recordDuration + 1
      this.setData({
        recordDuration: currentDuration,
        canStopRecording: currentDuration >= MIN_RECORD_DURATION
      })

      if (currentDuration >= MAX_RECORD_DURATION) {
        this.stopRecording()
      }
    }, 1000)

    this.setData({ recordTimer: timer })

    ctx.startRecord({
      maxDuration: MAX_RECORD_DURATION as number,
      success: function() {
        console.log('Recording started success')
      },
      fail: (error) => {
        console.error('Failed to start recording:', error)
        const timer = this.data.recordTimer as ReturnType<typeof setInterval> | null
        if (timer) {
          clearInterval(timer)
          this.setData({ recordTimer: null })
        }
        wx.showToast({
          title: '录制失败',
          icon: 'none'
        })
        this.resetRecordState()
      }
    })
  },

  stopRecording(): void {
    const ctx = this.data.cameraContext as WechatMiniprogram.CameraContext | null
    if (!ctx) return

    if (!this.data.isRecording) {
      console.log('未在录制状态')
      return
    }

    const timer = this.data.recordTimer as ReturnType<typeof setInterval> | null
    if (timer) {
      clearInterval(timer)
      this.setData({ recordTimer: null })
    }

    this.setData({
      isRecording: false,
      cameraTip: '录制完成，正在检查视频...',
      buttonState: 'analyzing' as ButtonState
    })

    ctx.stopRecord({
      success: (res) => {
        const systemInfo = wx.getSystemInfoSync()
        console.log('当前运行平台:', systemInfo.platform)
        console.log('stopRecord 返回:', res)
        const tempVideoPath = res.tempVideoPath
        const tempThumbPath = res.tempThumbPath
        console.log('tempVideoPath:', tempVideoPath)

        if (!tempVideoPath) {
          console.error('tempVideoPath 为空')
          wx.showToast({
            title: '视频录制失败，请重新录制',
            icon: 'none'
          })
          this.resetRecordState()
          return
        }

        this.checkRecordedVideo(tempVideoPath, tempThumbPath)
      },
      fail: (error) => {
        console.error('Failed to stop recording:', error)
        wx.showToast({
          title: '录制失败',
          icon: 'none'
        })
        this.resetRecordState()
      }
    })
  },

  resetRecordState(): void {
    this.setData({
      isRecording: false,
      isSubmitting: false,
      buttonState: 'idle' as ButtonState,
      canRecord: true
    })
    this.setCameraStatus('video_parse_failed')
  },

  checkRecordedVideo(videoPath: string, thumbPath: string): void {
    console.log('开始检查视频信息')
    wx.getVideoInfo({
      src: videoPath,
      success: (info) => {
        console.log('getVideoInfo success:', info)

        const duration = info.duration

        if (!duration || duration <= 0 || isNaN(duration)) {
          console.error('视频时长无效:', duration)
          
          const systemInfo = wx.getSystemInfoSync()
          console.log('当前运行平台:', systemInfo.platform)
          
          if (systemInfo.platform === 'devtools') {
            wx.showModal({
              title: '录制提示',
              content: '开发者工具录制视频可能无效，请使用真机调试或从相册选择视频测试。',
              showCancel: false,
              success: () => {
                this.resetRecordState()
              }
            })
          } else {
            wx.showToast({
              title: '视频录制失败，请重新录制',
              icon: 'none'
            })
            this.resetRecordState()
          }
          return
        }

        this.handleValidVideo(videoPath, thumbPath, duration, info.fps || 0)
      },
      fail: (error) => {
        console.error('getVideoInfo failed:', error)
        
        const systemInfo = wx.getSystemInfoSync()
        console.log('当前运行平台:', systemInfo.platform)
        
        if (systemInfo.platform === 'devtools') {
          wx.showModal({
            title: '录制提示',
            content: '开发者工具录制视频可能无法解析，请使用真机调试录制，或从相册选择视频测试。',
            showCancel: false,
            success: () => {
              this.resetRecordState()
            }
          })
        } else {
          wx.showToast({
            title: '视频信息读取失败，请重新录制',
            icon: 'none'
          })
          this.resetRecordState()
        }
      }
    })
  },

  handleValidVideo(videoPath: string, thumbPath: string, duration: number, fps: number): void {
    console.log('准备上传的视频路径:', videoPath)

    wx.getFileInfo({
      filePath: videoPath,
      success: (fileInfo) => {
        const video: VideoEntry = {
          url: videoPath,
          thumbUrl: thumbPath,
          name: getFileName(videoPath),
          size: fileInfo.size,
          sizeLabel: formatFileSize(fileInfo.size),
          duration: duration,
          fps: fps,
          durationLabel: `${duration.toFixed(1)}秒`,
          fpsLabel: fps ? `${fps}fps` : '未知'
        }

        this.setData({
          tongueVideo: video,
          showCameraMode: false,
          hasReport: false,
          report: null,
          reportView: emptyReportView(),
          tipsText: '',
          cameraTip: '正在上传分析...'
        })

        this.onSubmit()
      },
      fail: () => {
        const video: VideoEntry = {
          url: videoPath,
          thumbUrl: thumbPath,
          name: getFileName(videoPath),
          size: 0,
          sizeLabel: '未知',
          duration: duration,
          fps: fps,
          durationLabel: `${duration.toFixed(1)}秒`,
          fpsLabel: fps ? `${fps}fps` : '未知'
        }

        this.setData({
          tongueVideo: video,
          showCameraMode: false,
          hasReport: false,
          report: null,
          reportView: emptyReportView(),
          tipsText: '',
          cameraTip: '正在上传分析...'
        })

        this.onSubmit()
      }
    })
  },

  onChooseFromAlbum(): void {
    if (this.data.buttonState === 'analyzing') {
      console.log('正在上传分析中，请勿重复点击')
      return
    }

    if (this.data.isRecording) {
      console.log('正在录制中，请勿重复点击')
      return
    }

    wx.chooseMedia({
      count: 1,
      mediaType: ['video'],
      sourceType: ['album'],
      maxDuration: 20,
      camera: 'front',
      success: (res) => {
        const file = res.tempFiles[0] as WechatMiniprogram.MediaFile & {
          thumbTempFilePath?: string
        }

        if (!file) return

        wx.getVideoInfo({
          src: file.tempFilePath,
          success: (info) => {
            const video: VideoEntry = {
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

            const validationMessage = validateVideoEntry(video)
            if (validationMessage) {
              wx.showToast({
                title: validationMessage,
                icon: 'none'
              })
              return
            }

            this.setData({
              tongueVideo: video,
              showCameraMode: false,
              hasReport: false,
              report: null,
              reportView: emptyReportView(),
              tipsText: '',
              buttonState: 'analyzing' as ButtonState
            })

            this.onSubmit()
          },
          fail: () => {
            if (file.size > MAX_VIDEO_SIZE) {
              wx.showToast({
                title: '视频大小不能超过 5MB',
                icon: 'none'
              })
              return
            }

            const video: VideoEntry = {
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
              tongueVideo: video,
              showCameraMode: false,
              hasReport: false,
              report: null,
              reportView: emptyReportView(),
              tipsText: '',
              buttonState: 'analyzing' as ButtonState
            })

            this.onSubmit()
          }
        })
      },
      fail: () => {
        console.log('User cancelled album selection')
      }
    })
  },

  switchToCameraMode(): void {
    this.setData({
      showCameraMode: true,
      cameraStatus: 'init' as CameraStatusType,
      cameraTip: '正在启动摄像头',
      isRecording: false,
      recordDuration: 0,
      recordStartTime: 0,
      canRecord: true,
      faceRect: null,
      frameCount: 0,
      buttonState: 'idle' as ButtonState,
      canStopRecording: false
    })
  },

  onChooseImage(event: WechatMiniprogram.CustomEvent): void {
    const field = event.currentTarget.dataset.field as ImageField

    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: (res) => {
        const file = res.tempFiles[0]

        if (!file) return

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

  onChooseVideo(): void {
    wx.chooseMedia({
      count: 1,
      mediaType: ['video'],
      sourceType: ['album', 'camera'],
      maxDuration: 20,
      camera: 'front',
      success: (res) => {
        const file = res.tempFiles[0] as WechatMiniprogram.MediaFile & {
          thumbTempFilePath?: string
        }

        if (!file) return

        wx.getVideoInfo({
          src: file.tempFilePath,
          success: (info) => {
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
              showCameraMode: false,
              hasReport: false,
              report: null,
              reportView: emptyReportView(),
              tipsText: '',
              buttonState: 'analyzing' as ButtonState
            })

            this.onSubmit()
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
              showCameraMode: false,
              hasReport: false,
              report: null,
              reportView: emptyReportView(),
              tipsText: '',
              buttonState: 'analyzing' as ButtonState
            })

            this.onSubmit()
          }
        })
      }
    })
  },

  onSubmit(): void {
    if (!this.data.tongueVideo) {
      wx.showToast({
        title: '请上传舌苔视频',
        icon: 'none'
      })
      return
    }

    if (this.data.isSubmitting) {
      console.log('正在上传分析中，请勿重复点击')
      return
    }

    this.setData({
      isSubmitting: true,
      tipsText: '分析中，请稍候...'
    })

    uploadTongueVideo(this.data.tongueVideo.url)
      .then((data) => {
        const report = data.report
        if (!report) {
          throw new Error('未返回分析报告')
        }

        this.setData({
          report,
          reportView: buildReportView(report),
          hasReport: true,
          isSubmitting: false,
          tipsText: data.tips || '',
          buttonState: 'completed' as ButtonState
        })

        if (data.tips) {
          this.setData({
            reportScrollId: 'report-section'
          })
        }

        wx.showToast({
          title: '分析完成',
          icon: 'success'
        })
      })
      .catch((error) => {
        console.error('Upload failed:', error)

        const errorMessage = getErrorMessage(
          (error as { errorCode?: string }).errorCode,
          error.message
        )

        this.setData({
          isSubmitting: false,
          tipsText: '',
          buttonState: 'failed' as ButtonState
        })

        wx.showModal({
          title: '分析失败',
          content: errorMessage,
          showCancel: false
        })
      })
  },

  onDeleteMedia(event: WechatMiniprogram.CustomEvent): void {
    const field = event.currentTarget.dataset.field as MediaField

    this.setData({
      [field]: null,
      hasReport: false,
      report: null,
      reportView: emptyReportView(),
      tipsText: '',
      buttonState: 'idle' as ButtonState
    })
  },

  onRetry(): void {
    this.setData({
      tongueVideo: null,
      showCameraMode: true,
      cameraStatus: 'init' as CameraStatusType,
      cameraTip: '正在启动摄像头',
      isRecording: false,
      recordDuration: 0,
      recordStartTime: 0,
      canRecord: true,
      faceRect: null,
      frameCount: 0,
      buttonState: 'idle' as ButtonState,
      canStopRecording: false
    })
  },

  onHide(): void {
    console.log('Page onHide')
    this.stopFrameListener()
  },

  onUnload(): void {
    console.log('Page onUnload')
    this.stopFrameListener()
  }
})
