import { drawLottery, getLotteryStatus, getPointsStateSnapshot } from '../../utils/points-store'

type GameMode = 'wheel' | 'scratch'

type WheelPrize = {
  name: string
  rate: string
  color: string
}

type WheelSegmentView = WheelPrize & {
  angle: number
  style: string
  cardStyle: string
}

type ResultModalKind = 'wheel' | 'scratch'

const WHEEL_PRIZES: WheelPrize[] = [
  { name: '谢谢参与', rate: '35%', color: '#dff5ef' },
  { name: '5积分', rate: '25%', color: '#edf9f5' },
  { name: '10积分', rate: '20%', color: '#d8f4ec' },
  { name: '20积分', rate: '10%', color: '#c8efe4' },
  { name: '再抽一次', rate: '5%', color: '#edf9f5' },
  { name: '5元优惠券', rate: '5%', color: '#dff5ef' }
]

Page({
  data: {
    mode: 'wheel' as GameMode,
    balance: 0,
    drawCountToday: 0,
    drawLimitRemaining: 0,
    freeDrawAvailable: false,
    paidDrawCost: 60,
    wheelRotation: 0,
    wheelSpinning: false,
    wheelPrize: '',
    wheelMessage: '点击中间按钮开始转盘抽奖。',
    wheelResultDelta: 0,
    wheelExtraDrawTriggered: false,
    wheelSegments: [] as WheelSegmentView[],
    lastPrize: '',
    lastMessage: '今天还没有开始抽奖，快来试试吧。',
    lastDelta: 0,
    extraDrawTriggered: false,
    scratchReady: true,
    scratchCompleted: false,
    scratchCleared: false,
    scratchProgress: 0,
    scratchPrize: '',
    scratchMessage: '滑动手指揭晓奖励',
    scratchResultDelta: 0,
    scratchExtraDrawTriggered: false,
    scratchCanvasWidth: 300,
    scratchCanvasHeight: 180,
    scratchFlashVisible: false,
    resultModalVisible: false,
    resultModalKind: 'wheel' as ResultModalKind,
    resultModalTitle: '',
    resultModalPrize: '',
    resultModalMessage: '',
    resultModalDeltaText: '',
    resultModalBadge: '',
    resultModalHighlight: ''
  },

  scratchCanvasContext: null as WechatMiniprogram.CanvasContext | null,
  scratchGrid: [] as boolean[][],
  scratchGridSize: { cols: 12, rows: 6 },
  scratchDrawing: false,
  wheelTimer: null as number | null,
  flashTimer: null as number | null,

  onLoad() {
    this.initCanvasSize()
    this.initWheelSegments()
    this.refreshData()
  },

  onShow() {
    this.refreshData()
  },

  onUnload() {
    if (this.wheelTimer) {
      clearTimeout(this.wheelTimer)
      this.wheelTimer = null
    }
    if (this.flashTimer) {
      clearTimeout(this.flashTimer)
      this.flashTimer = null
    }
  },

  initCanvasSize() {
    const systemInfo = wx.getSystemInfoSync()
    const width = Math.max(280, Math.floor(systemInfo.windowWidth - 48))
    const height = 180
    this.setData({
      scratchCanvasWidth: width,
      scratchCanvasHeight: height
    })
    this.resetScratchGrid()
  },

  initWheelSegments() {
    const segmentCount = WHEEL_PRIZES.length
    const radius = 134
    const step = 360 / segmentCount

    const wheelSegments = WHEEL_PRIZES.map((item, index) => {
      const angle = -90 + step * index + step / 2
      return {
        ...item,
        angle,
        style: `transform: translate(-50%, -50%) rotate(${angle}deg) translateY(-${radius}rpx) rotate(${-angle}deg);`,
        cardStyle: `background: linear-gradient(180deg, rgba(255,255,255,0.98), ${item.color});`
      }
    })

    this.setData({
      wheelSegments
    })
  },

  refreshData() {
    const status = getLotteryStatus()
    const snapshot = getPointsStateSnapshot()
    const hasDrawToday = snapshot.lotteryDate === this.getTodayKey()

    this.setData({
      balance: status.balance,
      drawCountToday: status.drawCountToday,
      drawLimitRemaining: status.drawLimitRemaining,
      freeDrawAvailable: status.freeDrawAvailable,
      paidDrawCost: status.paidDrawCost,
      lastMessage: hasDrawToday ? this.data.lastMessage : '今天还没有开始抽奖，快来试试吧。',
      lastPrize: hasDrawToday ? this.data.lastPrize : '',
      lastDelta: hasDrawToday ? this.data.lastDelta : 0,
      extraDrawTriggered: hasDrawToday ? this.data.extraDrawTriggered : false
    })
  },

  getTodayKey() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  },

  switchMode(event: WechatMiniprogram.CustomEvent) {
    const mode = String(event.currentTarget.dataset.mode || 'wheel') as GameMode
    this.setData({ mode })
    if (mode === 'scratch' && this.data.scratchReady && !this.data.scratchCleared) {
      this.drawScratchCover()
    }
  },

  triggerResultModal(options: {
    kind: ResultModalKind
    prize: string
    message: string
    delta: number
    extraDrawTriggered: boolean
  }) {
    const deltaText = `${options.delta >= 0 ? '+' : ''}${options.delta} 积分变化`
    const badge = options.extraDrawTriggered ? '触发额外奖励' : options.kind === 'wheel' ? '转盘中奖' : '刮刮乐中奖'
    const highlight = options.kind === 'wheel' ? '大转盘结果已同步写入积分明细。' : '刮刮乐结果已同步写入积分明细。'

    this.setData({
      resultModalVisible: true,
      resultModalKind: options.kind,
      resultModalTitle: options.kind === 'wheel' ? '转盘中奖' : '刮刮乐彩票',
      resultModalPrize: options.prize,
      resultModalMessage: options.message,
      resultModalDeltaText: deltaText,
      resultModalBadge: badge,
      resultModalHighlight: highlight,
      scratchFlashVisible: true
    })

    if (this.flashTimer) {
      clearTimeout(this.flashTimer)
    }

    this.flashTimer = setTimeout(() => {
      this.setData({
        scratchFlashVisible: false
      })
    }, 850)
  },

  normalizeRotation(rotation: number) {
    const normalized = rotation % 360
    return normalized < 0 ? normalized + 360 : normalized
  },

  closeResultModal() {
    this.setData({
      resultModalVisible: false
    })
  },

  noop() {
    return
  },

  onWheelDrawTap() {
    if (this.data.wheelSpinning) {
      return
    }

    if (this.data.drawLimitRemaining <= 0) {
      wx.showToast({
        title: '今天抽奖次数已用完',
        icon: 'none'
      })
      return
    }

    const result = drawLottery()
    const prizeIndex = this.getPrizeIndex(result.prize)
    const step = 360 / WHEEL_PRIZES.length
    const currentRotation = this.normalizeRotation(this.data.wheelRotation)
    const targetAngle = -(prizeIndex * step + step / 2)
    const deltaAngle = targetAngle - currentRotation
    const spinCount = 4 + Math.floor(Math.random() * 2)
    const nextRotation = this.data.wheelRotation + spinCount * 360 + deltaAngle

    this.setData({
      wheelSpinning: true,
      wheelPrize: '',
      wheelMessage: '转盘飞速旋转中...',
      wheelResultDelta: 0,
      wheelExtraDrawTriggered: false,
      wheelRotation: nextRotation
    })

    this.wheelTimer = setTimeout(() => {
      this.setData({
        wheelSpinning: false,
        wheelPrize: result.prize,
        wheelMessage: result.message,
        wheelResultDelta: result.delta,
        wheelExtraDrawTriggered: result.extraDrawTriggered,
        lastPrize: result.prize,
        lastMessage: result.message,
        lastDelta: result.delta,
        extraDrawTriggered: result.extraDrawTriggered
      })

      this.triggerResultModal({
        kind: 'wheel',
        prize: result.prize,
        message: result.message,
        delta: result.delta,
        extraDrawTriggered: result.extraDrawTriggered
      })
      this.refreshData()
    }, 3000)
  },

  getPrizeIndex(prizeName: string) {
    const index = WHEEL_PRIZES.findIndex((item) => item.name === prizeName)
    return index >= 0 ? index : 0
  },

  resetScratchFlow() {
    this.scratchDrawing = false
    this.resetScratchGrid()
    this.clearScratchCanvas()
  },

  resetScratchGrid() {
    const { cols, rows } = this.scratchGridSize
    this.scratchGrid = Array.from({ length: rows }, () => Array.from({ length: cols }, () => false))
  },

  clearScratchCanvas() {
    if (!this.scratchCanvasContext) {
      this.scratchCanvasContext = wx.createCanvasContext('scratchCanvas', this)
    }

    const ctx = this.scratchCanvasContext
    ctx.clearRect(0, 0, this.data.scratchCanvasWidth, this.data.scratchCanvasHeight)
    ctx.draw()
  },

  drawScratchCover() {
    if (!this.scratchCanvasContext) {
      this.scratchCanvasContext = wx.createCanvasContext('scratchCanvas', this)
    }

    const ctx = this.scratchCanvasContext
    const width = this.data.scratchCanvasWidth
    const height = this.data.scratchCanvasHeight
    const radius = 24

    ctx.clearRect(0, 0, width, height)

    const metalGradient = ctx.createLinearGradient(0, 0, width, height)
    metalGradient.addColorStop(0, '#f0f5f3')
    metalGradient.addColorStop(0.18, '#cbd7d3')
    metalGradient.addColorStop(0.5, '#eef3f1')
    metalGradient.addColorStop(0.82, '#bac7c3')
    metalGradient.addColorStop(1, '#e6eeeb')
    ctx.setFillStyle(metalGradient)
    ctx.fillRect(0, 0, width, height)

    const shineGradient = ctx.createLinearGradient(0, 0, width, 0)
    shineGradient.addColorStop(0, 'rgba(255,255,255,0)')
    shineGradient.addColorStop(0.5, 'rgba(255,255,255,0.48)')
    shineGradient.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.setFillStyle(shineGradient)
    ctx.fillRect(0, 0, width, height)

    ctx.setStrokeStyle('rgba(0, 134, 113, 0.18)')
    ctx.setLineWidth(2)
    ctx.strokeRect(1, 1, width - 2, height - 2)

    ctx.setFillStyle('#1e332f')
    ctx.setFontSize(30)
    ctx.setTextAlign('center')
    ctx.fillText('刮开试试', width / 2, height / 2 - 8)
    ctx.setFontSize(22)
    ctx.setFillStyle('#5d736f')
    ctx.fillText('滑动手指揭晓奖励', width / 2, height / 2 + 26)

    ctx.beginPath()
    ctx.moveTo(radius, 0)
    ctx.lineTo(width - radius, 0)
    ctx.quadraticCurveTo(width, 0, width, radius)
    ctx.lineTo(width, height - radius)
    ctx.quadraticCurveTo(width, height, width - radius, height)
    ctx.lineTo(radius, height)
    ctx.quadraticCurveTo(0, height, 0, height - radius)
    ctx.lineTo(0, radius)
    ctx.quadraticCurveTo(0, 0, radius, 0)
    ctx.closePath()
    ctx.stroke()

    ctx.draw()
  },

  onScratchTouchStart(event: WechatMiniprogram.TouchEvent) {
    if (!this.data.scratchReady || this.data.scratchCleared) {
      return
    }

    if (this.data.drawLimitRemaining <= 0) {
      wx.showToast({
        title: '今天抽奖次数已用完',
        icon: 'none'
      })
      return
    }

    const touch = event.touches[0]
    this.scratchDrawing = true
    this.eraseScratchAt(touch.x, touch.y)
  },

  onScratchTouchMove(event: WechatMiniprogram.TouchEvent) {
    if (!this.scratchDrawing || !this.data.scratchReady || this.data.scratchCleared) {
      return
    }

    const touch = event.touches[0]
    this.eraseScratchAt(touch.x, touch.y)
  },

  onScratchTouchEnd() {
    this.scratchDrawing = false
  },

  eraseScratchAt(x: number, y: number) {
    if (!this.scratchCanvasContext) {
      return
    }

    const ctx = this.scratchCanvasContext
    const brushRadius = 18
    ctx.clearRect(x - brushRadius, y - brushRadius, brushRadius * 2, brushRadius * 2)
    ctx.draw(true)

    this.markScratchProgress(x, y)
  },

  markScratchProgress(x: number, y: number) {
    const { cols, rows } = this.scratchGridSize
    const width = this.data.scratchCanvasWidth
    const height = this.data.scratchCanvasHeight
    const cellWidth = width / cols
    const cellHeight = height / rows

    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const cellLeft = col * cellWidth
        const cellTop = row * cellHeight
        const cellRight = cellLeft + cellWidth
        const cellBottom = cellTop + cellHeight
        const near = x >= cellLeft - 8 && x <= cellRight + 8 && y >= cellTop - 8 && y <= cellBottom + 8
        if (near) {
          this.scratchGrid[row][col] = true
        }
      }
    }

    const scratchedCount = this.scratchGrid.reduce((sum, row) => sum + row.filter(Boolean).length, 0)
    const totalCount = cols * rows
    const progress = Math.min(100, Math.round((scratchedCount / totalCount) * 100))

    this.setData({
      scratchProgress: progress
    })

    if (progress >= 55 && !this.data.scratchCleared) {
      this.finishScratchGame()
    }
  },

  finishScratchGame() {
    if (this.data.scratchCleared) {
      return
    }

    const result = drawLottery()
    this.setData({
      scratchCompleted: true,
      scratchCleared: true,
      scratchPrize: result.prize,
      scratchMessage: result.message,
      scratchResultDelta: result.delta,
      scratchExtraDrawTriggered: result.extraDrawTriggered,
      lastPrize: result.prize,
      lastMessage: result.message,
      lastDelta: result.delta,
      extraDrawTriggered: result.extraDrawTriggered
    })
    this.clearScratchCanvas()

    this.triggerResultModal({
      kind: 'scratch',
      prize: result.prize,
      message: result.message,
      delta: result.delta,
      extraDrawTriggered: result.extraDrawTriggered
    })
    this.refreshData()
  },

  onBackTap() {
    wx.navigateBack({
      delta: 1
    })
  }
})
