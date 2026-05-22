type PointsSource = 'init' | 'signin' | 'task' | 'lottery' | 'exchange' | 'refund'

type PointsTaskId = 'profile_complete' | 'questionnaire_fill' | 'tongue_upload' | 'report_upload' | 'view_rules'

type TaskLimit = 'once' | 'daily'

interface PointsHistoryRecord {
  id: string
  type: 'get' | 'spend'
  source: PointsSource
  title: string
  delta: number
  note: string
  createdAt: string
  taskId?: PointsTaskId
}

interface PointsState {
  version: number
  userKey: string
  initialized: boolean
  initType: 'new' | 'old'
  initBonus: number
  initBreakdown: Array<{ label: string; points: number }>
  balance: number
  todayEarned: number
  weeklyEarned: number
  dailyDate: string
  weeklyKey: string
  signInDate: string
  signInDays: number
  lotteryDate: string
  lotteryCount: number
  taskClaims: Record<string, string>
  history: PointsHistoryRecord[]
  lastUpdatedAt: string
}

export interface PointsTaskView {
  id: PointsTaskId
  title: string
  desc: string
  points: number
  route?: string
  actionText: string
  claimed: boolean
  claimableToday: boolean
  note: string
}

export interface PointsSignInDayView {
  day: number
  points: number
  active: boolean
  today: boolean
  completed: boolean
}

export interface PointsExchangeItem {
  id: string
  name: string
  points: number
  description: string
  tag: string
  highlight: string
}

export interface PointsDashboard {
  balance: number
  todayEarned: number
  weeklyEarned: number
  signInDays: number
  initType: 'new' | 'old'
  initBonus: number
  initBreakdown: Array<{ label: string; points: number }>
  dailyLimitRemaining: number
  weeklyLimitRemaining: number
  historyCount: number
  signInDaysView: PointsSignInDayView[]
  tasks: PointsTaskView[]
  exchangeItems: PointsExchangeItem[]
}

export interface PointsActionResult {
  success: boolean
  delta: number
  balance: number
  message: string
  record?: PointsHistoryRecord | null
}

export interface PointsLotteryResult extends PointsActionResult {
  prize: string
  paidCost: number
  drawCountToday: number
  drawLimitRemaining: number
  extraDrawTriggered: boolean
}

interface RewardConfig {
  id: PointsTaskId
  title: string
  desc: string
  points: number
  limit: TaskLimit
  route?: string
  actionText: string
  note: string
}

interface ExchangeConfig {
  id: string
  name: string
  points: number
  description: string
  tag: string
  highlight: string
}

const STATE_VERSION = 1
const DAILY_EARN_LIMIT = 60
const WEEKLY_EARN_LIMIT = 200
const HISTORY_LIMIT = 300
const INIT_BASE_POINTS = 100
const SIGN_IN_POINTS = [5, 5, 10, 10, 10, 10, 20]

const STORAGE_PREFIX = 'user_points_state_v1'
const STORAGE_ACTIVE_USER_KEY = 'user_points_active_user_key'
const STORAGE_COMPAT_PREFIX = 'user_points'

const TASK_CONFIGS: Record<PointsTaskId, RewardConfig> = {
  profile_complete: {
    id: 'profile_complete',
    title: '完善个人资料',
    desc: '首次完善基础资料后可领取一次奖励。',
    points: 30,
    limit: 'once',
    route: '/pages/profile/edit',
    actionText: '去完善',
    note: '首次完善个人资料'
  },
  questionnaire_fill: {
    id: 'questionnaire_fill',
    title: '填写量表',
    desc: '每日完成一次量表填写可获得积分。',
    points: 15,
    limit: 'daily',
    route: '/pages/scale-form/scale-form',
    actionText: '去填写',
    note: '完成量表填写'
  },
  tongue_upload: {
    id: 'tongue_upload',
    title: '上传舌苔',
    desc: '每日首次上传舌苔可获得积分。',
    points: 10,
    limit: 'daily',
    route: '/pages/tongue-upload/tongue-upload',
    actionText: '去上传',
    note: '完成舌苔上传'
  },
  report_upload: {
    id: 'report_upload',
    title: '上传检查报告',
    desc: '每日首次上传检查报告可获得积分。',
    points: 10,
    limit: 'daily',
    route: '/pages/report-upload/report-upload',
    actionText: '去上传',
    note: '完成检查报告上传'
  },
  view_rules: {
    id: 'view_rules',
    title: '查看积分规则',
    desc: '首次查看积分规则可领取一次奖励。',
    points: 5,
    limit: 'once',
    actionText: '查看并领取',
    note: '查看积分规则'
  }
}

const EXCHANGE_CONFIGS: ExchangeConfig[] = [
  {
    id: 'knowledge-pack',
    name: '健康科普资料包',
    points: 30,
    description: '精选健康科普资料，适合日常阅读与学习。',
    tag: '入门',
    highlight: '轻量学习'
  },
  {
    id: 'lottery-ticket',
    name: '抽奖次数1次',
    points: 60,
    description: '解锁一次幸运抽奖机会，继续积累积分。',
    tag: '趣味',
    highlight: '活动加码'
  },
  {
    id: 'coupon-5',
    name: '5元优惠券',
    points: 150,
    description: '适合日常服务抵扣的通用优惠权益。',
    tag: '优惠',
    highlight: '轻松抵扣'
  },
  {
    id: 'coupon-10',
    name: '10元优惠券',
    points: 280,
    description: '更高额度的通用优惠权益，适合长期积累兑换。',
    tag: '优惠',
    highlight: '高性价比'
  },
  {
    id: 'report-pack',
    name: '报告整理权益',
    points: 300,
    description: '适合日常资料整理与个人健康档案管理使用。',
    tag: '资料',
    highlight: '整理服务'
  },
  {
    id: 'service-voucher',
    name: '健康服务抵扣券',
    points: 500,
    description: '用于平台健康服务场景的通用抵扣权益。',
    tag: '权益',
    highlight: '通用抵扣'
  },
  {
    id: 'gift-pack',
    name: '平台礼品',
    points: 800,
    description: '平台精选礼品兑换权益，适合长期积累兑换。',
    tag: '礼品',
    highlight: '精选礼遇'
  },
  {
    id: 'premium-pass',
    name: '高级权益券',
    points: 1000,
    description: '平台高级权益体验券，适合高积分用户兑换。',
    tag: '高级',
    highlight: '长期回馈'
  }
]

const LOTTERY_CONFIG = [
  { name: '谢谢参与', weight: 35, points: 0 },
  { name: '5积分', weight: 25, points: 5 },
  { name: '10积分', weight: 20, points: 10 },
  { name: '20积分', weight: 10, points: 20 },
  { name: '再抽一次', weight: 5, points: 0 },
  { name: '5元优惠券', weight: 5, points: 0 }
]

function getAppInstance(): any {
  try {
    return getApp<any>()
  } catch {
    return {}
  }
}

function getCurrentUserKey(): string {
  const app = getAppInstance()
  const profile = app?.globalData?.userProfile || {}
  const userId = profile.userId || app?.globalData?.userId || wx.getStorageSync('USER_ID') || wx.getStorageSync('userId') || ''
  const userCode = profile.userCode || app?.globalData?.userCode || wx.getStorageSync('USER_CODE') || wx.getStorageSync('userCode') || ''
  const rawKey = String(userId || userCode || 'guest').trim()
  return rawKey || 'guest'
}

function getStateKey(userKey: string) {
  return `${STORAGE_PREFIX}:${userKey}`
}

function getTodayKey(date = new Date()) {
  return formatDate(date)
}

function getWeekKey(date = new Date()) {
  const current = new Date(date)
  const day = current.getDay()
  const diff = day === 0 ? -6 : 1 - day
  current.setDate(current.getDate() + diff)
  return formatDate(current)
}

function pad(num: number) {
  return String(num).padStart(2, '0')
}

function formatDate(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function formatDateTime(date = new Date()) {
  return `${formatDate(date)} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function createId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function safeReadObject(raw: any): Record<string, any> {
  if (!raw) return {}
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch {
      return {}
    }
  }
  if (typeof raw === 'object') return raw
  return {}
}

function safeReadArray(raw: any) {
  if (Array.isArray(raw)) return raw
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}

function isFilled(value: any) {
  if (value === null || value === undefined) return false
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return Number.isFinite(value)
  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed !== '' && trimmed !== '未知' && trimmed !== '请选择'
  }
  return true
}

function hasProfileCompletionEvidence(profile: Record<string, any>) {
  return [
    isFilled(profile.avatarUrl) && profile.avatarUrl !== '/assets/icons/mine.png',
    isFilled(profile.nickname) && profile.nickname !== '用户昵称',
    isFilled(profile.userCode) || isFilled(profile.userId),
    isFilled(profile.gender) && profile.gender !== 'unknown',
    isFilled(profile.birthday),
    profile.hasPhone === true,
    profile.hasIdCard === true
  ].every(Boolean)
}

function collectInitEvidence() {
  const profile = safeReadObject(wx.getStorageSync('USER_PROFILE'))
  let storageKeys: string[] = []
  try {
    storageKeys = wx.getStorageInfoSync().keys || []
  } catch {
    storageKeys = []
  }

  const hasQuestionnaireHistory = storageKeys.some((key) => key.toLowerCase().includes('questionnaire') && !key.startsWith('user_points'))
  const hasTongueHistory = storageKeys.some((key) => key.toLowerCase().includes('tongue') && !key.startsWith('user_points'))
  const hasReportHistory = storageKeys.some((key) => key.toLowerCase().includes('report') && !key.startsWith('user_points'))
  const hasProfile = hasProfileCompletionEvidence(profile)

  const breakdown: Array<{ label: string; points: number }> = []
  if (hasProfile) {
    breakdown.push({ label: '完善个人资料', points: 30 })
  }
  if (hasQuestionnaireHistory) {
    breakdown.push({ label: '历史填写量表', points: 30 })
  }
  if (hasTongueHistory) {
    breakdown.push({ label: '历史上传舌苔', points: 20 })
  }
  if (hasReportHistory) {
    breakdown.push({ label: '历史上传检查报告', points: 20 })
  }

  return {
    initType: breakdown.length > 0 ? ('old' as const) : ('new' as const),
    extraBonus: Math.min(200, breakdown.reduce((sum, item) => sum + item.points, 0)),
    breakdown,
    hasProfile
  }
}

function defaultState(userKey: string): PointsState {
  return {
    version: STATE_VERSION,
    userKey,
    initialized: false,
    initType: 'new',
    initBonus: 0,
    initBreakdown: [],
    balance: 0,
    todayEarned: 0,
    weeklyEarned: 0,
    dailyDate: getTodayKey(),
    weeklyKey: getWeekKey(),
    signInDate: '',
    signInDays: 0,
    lotteryDate: getTodayKey(),
    lotteryCount: 0,
    taskClaims: {},
    history: [],
    lastUpdatedAt: formatDateTime()
  }
}

function normalizeState(raw: any, userKey: string): PointsState {
  const base = defaultState(userKey)
  const state = safeReadObject(raw)

  return {
    ...base,
    ...state,
    version: STATE_VERSION,
    userKey,
    initialized: Boolean(state.initialized),
    initType: state.initType === 'old' ? 'old' : 'new',
    initBonus: Number(state.initBonus || 0),
    initBreakdown: Array.isArray(state.initBreakdown) ? state.initBreakdown : [],
    balance: Number(state.balance || 0),
    todayEarned: Number(state.todayEarned || 0),
    weeklyEarned: Number(state.weeklyEarned || 0),
    dailyDate: String(state.dailyDate || base.dailyDate),
    weeklyKey: String(state.weeklyKey || base.weeklyKey),
    signInDate: String(state.signInDate || ''),
    signInDays: Number(state.signInDays || 0),
    lotteryDate: String(state.lotteryDate || base.lotteryDate),
    lotteryCount: Number(state.lotteryCount || 0),
    taskClaims: safeReadObject(state.taskClaims),
    history: safeReadArray(state.history) as PointsHistoryRecord[],
    lastUpdatedAt: String(state.lastUpdatedAt || base.lastUpdatedAt)
  }
}

function syncCompatKeys(state: PointsState) {
  wx.setStorageSync('user_points_initialized', state.initialized ? '1' : '0')
  wx.setStorageSync('user_points_total', state.balance)
  wx.setStorageSync('user_points_history', state.history)
  wx.setStorageSync('user_points_signin_date', state.signInDate)
  wx.setStorageSync('user_points_signin_days', state.signInDays)
  wx.setStorageSync('user_points_daily_earned', state.todayEarned)
  wx.setStorageSync('user_points_weekly_earned', state.weeklyEarned)
}

function saveState(state: PointsState) {
  state.lastUpdatedAt = formatDateTime()
  wx.setStorageSync(getStateKey(state.userKey), state)
  wx.setStorageSync(STORAGE_ACTIVE_USER_KEY, state.userKey)
  syncCompatKeys(state)
  return state
}

function readState(userKey = getCurrentUserKey()) {
  const raw = wx.getStorageSync(getStateKey(userKey))
  if (raw) {
    return normalizeState(raw, userKey)
  }

  const fallback = wx.getStorageSync('user_points_state_v1')
  if (fallback) {
    return normalizeState(fallback, userKey)
  }

  return defaultState(userKey)
}

function refreshDailyAndWeekly(state: PointsState) {
  const todayKey = getTodayKey()
  const weekKey = getWeekKey()

  if (state.dailyDate !== todayKey) {
    state.dailyDate = todayKey
    state.todayEarned = 0
    state.lotteryCount = 0
    state.lotteryDate = todayKey
  }

  if (state.weeklyKey !== weekKey) {
    state.weeklyKey = weekKey
    state.weeklyEarned = 0
  }
}

function pushHistory(state: PointsState, record: PointsHistoryRecord) {
  state.history = [record, ...state.history].slice(0, HISTORY_LIMIT)
}

function writeDeltaRecord(
  state: PointsState,
  options: {
    source: PointsSource
    title: string
    delta: number
    note: string
    taskId?: PointsTaskId
  }
) {
  const record: PointsHistoryRecord = {
    id: createId(),
    type: options.delta >= 0 ? 'get' : 'spend',
    source: options.source,
    title: options.title,
    delta: options.delta,
    note: options.note,
    createdAt: formatDateTime(),
    taskId: options.taskId
  }

  pushHistory(state, record)
  return record
}

function applyEarnPoints(
  state: PointsState,
  amount: number,
  options: {
    source: PointsSource
    title: string
    note: string
    countTowardLimits?: boolean
    taskId?: PointsTaskId
  }
): PointsActionResult {
  const positiveAmount = Math.max(0, Math.floor(Number(amount || 0)))
  if (positiveAmount <= 0) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '积分未变化',
      record: null
    }
  }

  refreshDailyAndWeekly(state)

  const countTowardLimits = options.countTowardLimits !== false
  const dailyRemain = countTowardLimits ? Math.max(0, DAILY_EARN_LIMIT - state.todayEarned) : positiveAmount
  const weeklyRemain = countTowardLimits ? Math.max(0, WEEKLY_EARN_LIMIT - state.weeklyEarned) : positiveAmount
  const actual = Math.min(positiveAmount, dailyRemain, weeklyRemain)

  if (actual <= 0) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '今日或本周积分已达上限',
      record: null
    }
  }

  state.balance += actual
  if (countTowardLimits) {
    state.todayEarned += actual
    state.weeklyEarned += actual
  }

  const note = actual < positiveAmount
    ? `${options.note}，因今日/本周上限仅发放 ${actual} 积分`
    : options.note

  const record = writeDeltaRecord(state, {
    source: options.source,
    title: options.title,
    delta: actual,
    note,
    taskId: options.taskId
  })
  saveState(state)

  return {
    success: true,
    delta: actual,
    balance: state.balance,
    message: actual < positiveAmount ? `已发放 ${actual} 积分（受今日/本周上限影响）` : `已发放 ${actual} 积分`,
    record
  }
}

function applySpendPoints(
  state: PointsState,
  amount: number,
  options: {
    source: PointsSource
    title: string
    note: string
  }
): PointsActionResult {
  const spendAmount = Math.max(0, Math.floor(Number(amount || 0)))
  if (spendAmount <= 0) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '扣减金额不正确',
      record: null
    }
  }

  if (state.balance < spendAmount) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '积分不足',
      record: null
    }
  }

  state.balance -= spendAmount
  const record = writeDeltaRecord(state, {
    source: options.source,
    title: options.title,
    delta: -spendAmount,
    note: options.note
  })
  saveState(state)

  return {
    success: true,
    delta: -spendAmount,
    balance: state.balance,
    message: `已扣除 ${spendAmount} 积分`,
    record
  }
}

function ensureInitializedState(): PointsState {
  const userKey = getCurrentUserKey()
  const state = readState(userKey)

  if (state.initialized) {
    refreshDailyAndWeekly(state)
    saveState(state)
    return state
  }

  const initEvidence = collectInitEvidence()
  const initBonus = INIT_BASE_POINTS + initEvidence.extraBonus

  state.initialized = true
  state.initType = initEvidence.initType
  state.initBonus = initBonus
  state.initBreakdown = [
    {
      label: initEvidence.initType === 'new' ? '新手积分' : '上线体验积分',
      points: INIT_BASE_POINTS
    },
    ...initEvidence.breakdown
  ]
  state.taskClaims = initEvidence.hasProfile ? { profile_complete: 'once' } : {}
  state.balance = initBonus
  state.todayEarned = 0
  state.weeklyEarned = 0
  state.dailyDate = getTodayKey()
  state.weeklyKey = getWeekKey()
  state.signInDate = ''
  state.signInDays = 0
  state.lotteryDate = getTodayKey()
  state.lotteryCount = 0

  writeDeltaRecord(state, {
    source: 'init',
    title: initEvidence.initType === 'new' ? '新手积分初始化' : '上线体验积分初始化',
    delta: initBonus,
    note: initEvidence.initType === 'new'
      ? '首次进入积分商城赠送新手积分'
      : `首次进入积分商城赠送上线体验积分，历史补发 ${initEvidence.extraBonus} 积分`
  })

  saveState(state)
  return state
}

function getTaskClaimValue(state: PointsState, taskId: PointsTaskId) {
  return String(state.taskClaims[taskId] || '')
}

function buildTaskViews(state: PointsState): PointsTaskView[] {
  const todayKey = getTodayKey()

  return (Object.keys(TASK_CONFIGS) as PointsTaskId[]).map((taskId) => {
    const config = TASK_CONFIGS[taskId]
    const claimValue = getTaskClaimValue(state, taskId)
    const claimed = config.limit === 'once' ? Boolean(claimValue) : claimValue === todayKey

    return {
      id: taskId,
      title: config.title,
      desc: config.desc,
      points: config.points,
      route: config.route,
      actionText: claimed ? '已完成' : config.actionText,
      claimed,
      claimableToday: !claimed,
      note: config.note
    }
  })
}

function buildSignInDaysView(state: PointsState): PointsSignInDayView[] {
  const todayKey = getTodayKey()
  const todayIndex = Math.min(Math.max(state.signInDays || 0, 1), 7)

  return SIGN_IN_POINTS.map((points, index) => {
    const day = index + 1
    const completed = state.signInDays >= day

    return {
      day,
      points,
      active: state.signInDays === day,
      today: state.signInDate === todayKey && todayIndex === day,
      completed
    }
  })
}

function getExchangeItems(): PointsExchangeItem[] {
  return EXCHANGE_CONFIGS.map((item) => ({ ...item }))
}

function pickLotteryPrize() {
  const total = LOTTERY_CONFIG.reduce((sum, item) => sum + item.weight, 0)
  let cursor = Math.random() * total

  for (const item of LOTTERY_CONFIG) {
    cursor -= item.weight
    if (cursor <= 0) {
      return item
    }
  }

  return LOTTERY_CONFIG[0]
}

function drawLotteryOnce(state: PointsState, isBonusDraw = false, allowBonusChain = true): PointsLotteryResult {
  refreshDailyAndWeekly(state)

  const todayKey = getTodayKey()
  if (state.lotteryDate !== todayKey) {
    state.lotteryDate = todayKey
    state.lotteryCount = 0
  }

  if (state.lotteryCount >= 5) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '今日抽奖次数已用完',
      prize: '',
      paidCost: 0,
      drawCountToday: state.lotteryCount,
      drawLimitRemaining: 0,
      extraDrawTriggered: false,
      record: null
    }
  }

  const isFreeDraw = state.lotteryCount === 0 || isBonusDraw
  const paidCost = isFreeDraw ? 0 : 60

  if (!isFreeDraw) {
    const spendResult = applySpendPoints(state, paidCost, {
      source: 'lottery',
      title: '抽奖消耗',
      note: '额外抽奖消耗 60 积分'
    })
    if (!spendResult.success) {
      return {
        success: false,
        delta: 0,
        balance: state.balance,
        message: '积分不足，无法继续抽奖',
        prize: '',
        paidCost,
        drawCountToday: state.lotteryCount,
        drawLimitRemaining: Math.max(0, 5 - state.lotteryCount),
        extraDrawTriggered: false,
        record: null
      }
    }
  }

  state.lotteryCount += 1
  const prize = pickLotteryPrize()
  let prizeMessage = ''
  let prizeDelta = 0

  if (prize.name === '谢谢参与') {
    prizeMessage = '谢谢参与'
  } else if (prize.name === '5元优惠券') {
    prizeMessage = '获得 5 元优惠券'
  } else if (prize.name === '再抽一次') {
    prizeMessage = '获得再抽一次机会'
  } else {
    prizeMessage = `获得 ${prize.points} 积分`
    prizeDelta = prize.points
  }

  let record: PointsHistoryRecord | null = null

  if (prize.points > 0) {
    const earnResult = applyEarnPoints(state, prize.points, {
      source: 'lottery',
      title: `抽奖：${prize.name}`,
      note: `抽奖获得 ${prize.name}`,
      countTowardLimits: true
    })
    record = earnResult.record || null
    prizeDelta = earnResult.success ? earnResult.delta : 0
  } else {
    record = writeDeltaRecord(state, {
      source: 'lottery',
      title: `抽奖：${prize.name}`,
      delta: 0,
      note: prizeMessage
    })
    saveState(state)
  }

  if (prize.name === '再抽一次' && allowBonusChain && state.lotteryCount < 5) {
    writeDeltaRecord(state, {
      source: 'lottery',
      title: '抽奖：再抽一次',
      delta: 0,
      note: '触发一次额外抽奖机会'
    })
    saveState(state)

    const bonusResult = drawLotteryOnce(state, true, false)
    return {
      ...bonusResult,
      success: bonusResult.success,
      delta: bonusResult.delta - paidCost,
      balance: state.balance,
      prize: bonusResult.prize,
      paidCost,
      drawCountToday: bonusResult.drawCountToday,
      drawLimitRemaining: bonusResult.drawLimitRemaining,
      extraDrawTriggered: true,
      message: `再抽一次，${bonusResult.message}`,
      record: bonusResult.record
    }
  }

  return {
    success: true,
    delta: prizeDelta - paidCost,
    balance: state.balance,
    message: prizeMessage,
    prize: prize.name,
    paidCost,
    drawCountToday: state.lotteryCount,
    drawLimitRemaining: Math.max(0, 5 - state.lotteryCount),
    extraDrawTriggered: false,
    record
  }
}

export function completePointsTask(taskId: PointsTaskId): PointsActionResult {
  const config = TASK_CONFIGS[taskId]
  const state = ensureInitializedState()
  refreshDailyAndWeekly(state)

  if (taskId === 'profile_complete' && !hasProfileCompletionEvidence(safeReadObject(wx.getStorageSync('USER_PROFILE')))) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '资料还未完善，请补充后再领取',
      record: null
    }
  }

  const todayKey = getTodayKey()
  const currentClaim = String(state.taskClaims[taskId] || '')

  if (config.limit === 'once' && currentClaim) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '已领取过该奖励',
      record: null
    }
  }

  if (config.limit === 'daily' && currentClaim === todayKey) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '今日已领取过该奖励',
      record: null
    }
  }

  const result = applyEarnPoints(state, config.points, {
    source: 'task',
    title: config.title,
    note: config.note,
    countTowardLimits: true,
    taskId
  })

  if (result.success) {
    state.taskClaims[taskId] = config.limit === 'once' ? 'once' : todayKey
    saveState(state)
  }

  return {
    ...result,
    message: result.success ? `${config.title}奖励已领取` : result.message
  }
}

export function completePointsSignIn(): PointsActionResult {
  const state = ensureInitializedState()
  refreshDailyAndWeekly(state)

  const todayKey = getTodayKey()
  if (state.signInDate === todayKey) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '今天已经签到过了',
      record: null
    }
  }

  const yesterdayKey = getTodayKey(new Date(Date.now() - 24 * 60 * 60 * 1000))
  const nextDays = state.signInDate === yesterdayKey ? (state.signInDays >= 7 ? 1 : state.signInDays + 1) : 1
  const reward = SIGN_IN_POINTS[nextDays - 1] || 5

  state.signInDate = todayKey
  state.signInDays = nextDays

  const result = applyEarnPoints(state, reward, {
    source: 'signin',
    title: `第 ${nextDays} 天签到`,
    note: `七天签到第 ${nextDays} 天奖励`,
    countTowardLimits: true
  })

  if (result.success) {
    saveState(state)
  }

  return {
    ...result,
    message: result.success ? `签到成功，获得 ${result.delta} 积分` : result.message
  }
}

export function drawLottery(): PointsLotteryResult {
  const state = ensureInitializedState()
  return drawLotteryOnce(state)
}

export function redeemExchangeItem(itemId: string): PointsActionResult {
  const item = EXCHANGE_CONFIGS.find((entry) => entry.id === itemId)
  const state = ensureInitializedState()

  if (!item) {
    return {
      success: false,
      delta: 0,
      balance: state.balance,
      message: '未找到该兑换商品',
      record: null
    }
  }

  const result = applySpendPoints(state, item.points, {
    source: 'exchange',
    title: `兑换：${item.name}`,
    note: `兑换商品 ${item.name}`
  })

  return {
    ...result,
    message: result.success ? `兑换成功，已扣除 ${item.points} 积分` : `还差 ${Math.max(0, item.points - state.balance)} 积分`
  }
}

export function getPointsDashboard(): PointsDashboard {
  const state = ensureInitializedState()
  return {
    balance: state.balance,
    todayEarned: state.todayEarned,
    weeklyEarned: state.weeklyEarned,
    signInDays: state.signInDays,
    initType: state.initType,
    initBonus: state.initBonus,
    initBreakdown: clone(state.initBreakdown),
    dailyLimitRemaining: Math.max(0, DAILY_EARN_LIMIT - state.todayEarned),
    weeklyLimitRemaining: Math.max(0, WEEKLY_EARN_LIMIT - state.weeklyEarned),
    historyCount: state.history.length,
    signInDaysView: buildSignInDaysView(state),
    tasks: buildTaskViews(state),
    exchangeItems: getExchangeItems()
  }
}

export function getPointsHistoryRecords() {
  const state = ensureInitializedState()
  return clone(state.history)
}

export function getPointsExchangeItems() {
  return clone(EXCHANGE_CONFIGS)
}

export function getPointsExchangeItem(itemId: string) {
  return EXCHANGE_CONFIGS.find((item) => item.id === itemId) || null
}

export function getTaskById(taskId: PointsTaskId) {
  return TASK_CONFIGS[taskId] || null
}

export function getPointsTaskViews(): PointsTaskView[] {
  return buildTaskViews(ensureInitializedState())
}

export function getLotteryStatus() {
  const state = ensureInitializedState()
  refreshDailyAndWeekly(state)

  const todayKey = getTodayKey()
  if (state.lotteryDate !== todayKey) {
    state.lotteryDate = todayKey
    state.lotteryCount = 0
    saveState(state)
  }

  return {
    balance: state.balance,
    drawCountToday: state.lotteryCount,
    drawLimitRemaining: Math.max(0, 5 - state.lotteryCount),
    freeDrawAvailable: state.lotteryCount === 0,
    paidDrawCost: 60
  }
}

export function getPointsStateSnapshot() {
  const state = ensureInitializedState()
  return clone(state)
}

export function formatPointsDelta(delta: number) {
  const value = Number(delta || 0)
  return value > 0 ? `+${value}` : `${value}`
}

export function getPointsTimelineLabel(source: PointsSource) {
  const labelMap: Record<PointsSource, string> = {
    init: '初始化',
    signin: '签到',
    task: '任务',
    lottery: '抽奖',
    exchange: '兑换',
    refund: '退回'
  }
  return labelMap[source]
}

export function getPointsTaskLabel(taskId: PointsTaskId) {
  return TASK_CONFIGS[taskId]?.title || ''
}
