import { completePointsTask } from '../../utils/points-store'

type QuestionnaireOption = {
  value: string
  label: string
}

type QuestionnaireQuestion = {
  subjectId: string
  title: string
  isRequired?: boolean
  type?: string
  options: QuestionnaireOption[]
}

function normalizeAnswerValue(rawValue: unknown) {
  if (rawValue === null || rawValue === undefined) {
    return ''
  }

  return String(rawValue)
}

function extractAnswerValue(question: any) {
  const directValue =
    question.answerValue !== undefined && question.answerValue !== null ? question.answerValue :
    question.answer !== undefined && question.answer !== null ? question.answer :
    question.value !== undefined && question.value !== null ? question.value :
    question.selectedValue !== undefined && question.selectedValue !== null ? question.selectedValue :
    question.selectedOptionValue

  if (directValue !== undefined && directValue !== null && directValue !== '') {
    return normalizeAnswerValue(directValue)
  }

  if (question.answer && typeof question.answer === 'object') {
    const nestedValue =
      question.answer.value !== undefined && question.answer.value !== null ? question.answer.value :
      question.answer.answerValue !== undefined && question.answer.answerValue !== null ? question.answer.answerValue :
      question.answer.optionValue

    if (nestedValue !== undefined && nestedValue !== null && nestedValue !== '') {
      return normalizeAnswerValue(nestedValue)
    }
  }

  return ''
}

function buildInitialAnswers(questions: QuestionnaireQuestion[]) {
  const initialAnswers: Record<string, string> = {}

  questions.forEach((question) => {
    initialAnswers[question.subjectId] = ''
  })

  return initialAnswers
}

function hasAnswer(value: unknown) {
  return String(value ?? '').trim() !== ''
}

function countAnsweredQuestions(answers: Record<string, string>) {
  return Object.values(answers).filter((value) => hasAnswer(value)).length
}

function calcProgressPercent(currentIndex: number, totalCount: number) {
  if (!totalCount) {
    return 0
  }

  return Math.round(((currentIndex + 1) / totalCount) * 100)
}

function getCurrentUserId(): number | null {
  const app = getApp<IAppOption>()
  const globalUserId = app?.globalData?.userId
  const storageUserId = wx.getStorageSync('USER_ID')
  const rawUserId = globalUserId || storageUserId
  const parsedUserId = Number(rawUserId)
  return Number.isFinite(parsedUserId) && parsedUserId > 0 ? parsedUserId : null
}

Page({
  data: {
    recordId: '',
    templateId: '',
    questionnaireId: '',
    doctorId: '',
    patientId: '',
    doctorName: '',
    diseaseType: '',
    diseaseName: '',
    visitType: '',
    visitTypeLabel: '',
    questionnaireName: '',
    description: '',
    questions: [] as QuestionnaireQuestion[],
    currentQuestionIndex: 0,
    currentQuestion: null as QuestionnaireQuestion | null,
    totalQuestions: 0,
    answers: {} as Record<string, string>,
    answeredCount: 0,
    progressPercent: 0,
    loading: true,
    submitted: false,
    questionnaireStatus: '',
    isRefilling: false,
    submitting: false
  },
  onLoad(options: {
    recordId?: string
    doctorId?: string
    patientId?: string
    questionnaireId?: string
    doctorName?: string
    diseaseType?: string
    diseaseName?: string
    visitType?: string
    visitTypeLabel?: string
  }) {
    if (options && options.recordId) {
      console.log('[questionnaire-onLoad] questionnaireId =', options.questionnaireId)
      this.setData({
        recordId: options.recordId,
        templateId: '',
        questionnaireId: options.questionnaireId || '',
        doctorId: options.doctorId || '',
        patientId: options.patientId || '',
        doctorName: options.doctorName ? decodeURIComponent(options.doctorName) : '',
        diseaseType: options.diseaseType ? decodeURIComponent(options.diseaseType) : '',
        diseaseName: options.diseaseName ? decodeURIComponent(options.diseaseName) : '',
        visitType: options.visitType ? decodeURIComponent(options.visitType) : '',
        visitTypeLabel: options.visitTypeLabel ? decodeURIComponent(options.visitTypeLabel) : ''
      })
      this.loadQuestionnaire()
    }
  },
  setCurrentQuestion(questions: QuestionnaireQuestion[], nextIndex: number) {
    const safeIndex = Math.max(0, Math.min(nextIndex, Math.max(questions.length - 1, 0)))
    const currentQuestion = questions[safeIndex] || null

    this.setData({
      currentQuestionIndex: safeIndex,
      currentQuestion,
      progressPercent: calcProgressPercent(safeIndex, questions.length)
    })
  },
  async loadQuestionnaire() {
    const { recordId } = this.data
    wx.showLoading({ title: '加载中...' })

    try {
      const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
        wx.request({
          url: `https://miniprogram.huiliaoyiyuan.com/api/questionnaires/detail?recordId=${recordId}`,
          method: 'GET',
          success: resolve,
          fail: reject
        })
      })

      if (response.statusCode === 200 && response.data) {
        const data = response.data as any
        const responseData = data || {}
        const questionsArray = Array.isArray(responseData.questions) ? responseData.questions : []

        const questions = questionsArray.map((item: any) => ({
          subjectId: String(item.id || item.subjectId || item.questionId || ''),
          title: item.title || item.questionText || '',
          type: item.type,
          isRequired: Boolean(item.isRequired),
          options: Array.isArray(item.options)
            ? item.options.map((option: any, optionIndex: number) => ({
                value: String(
                  option.value !== undefined && option.value !== null
                    ? option.value
                    : option.id !== undefined && option.id !== null
                      ? option.id
                      : optionIndex + 1
                ),
                label: String(
                  option.label !== undefined && option.label !== null
                    ? option.label
                    : option.title !== undefined && option.title !== null
                      ? option.title
                      : option.text !== undefined && option.text !== null
                        ? option.text
                        : ''
                )
              }))
            : []
        }))

        const totalQuestions = questions.length
        const submitted = responseData.status === 'completed'
        const questionnaireId = this.data.questionnaireId || String(responseData.questionnaireId || '')

        this.setData({
          recordId: String(responseData.recordId || recordId),
          templateId: String(responseData.templateId || ''),
          questionnaireId,
          questionnaireName: responseData.questionnaireName || '',
          description: responseData.description || '',
          questions,
          totalQuestions,
          answers: buildInitialAnswers(questions),
          answeredCount: 0,
          submitted,
          questionnaireStatus: responseData.status || '',
          isRefilling: false,
          loading: false
        })

        this.setCurrentQuestion(questions, 0)
      } else {
        wx.showToast({ title: '加载失败', icon: 'none' })
        this.setData({ loading: false })
      }
    } catch (error) {
      wx.showToast({ title: '网络错误', icon: 'none' })
      this.setData({ loading: false })
    } finally {
      wx.hideLoading()
    }
  },
  handleOptionChange(e: WechatMiniprogram.CustomEvent) {
    const subjectId = String(e.currentTarget.dataset.subjectId || '')
    const value = String(e.detail.value || '')

    const nextAnswers = {
      ...this.data.answers,
      [subjectId]: value
    }

    const answeredCount = countAnsweredQuestions(nextAnswers)

    this.setData({
      answers: nextAnswers,
      answeredCount
    })
  },
  handleTextInput(e: WechatMiniprogram.CustomEvent) {
    const subjectId = String(e.currentTarget.dataset.subjectId || '')
    const value = String(e.detail.value || '')

    const nextAnswers = {
      ...this.data.answers,
      [subjectId]: value
    }

    const answeredCount = countAnsweredQuestions(nextAnswers)

    this.setData({
      answers: nextAnswers,
      answeredCount
    })
  },
  startRefillQuestionnaire() {
    const { questions } = this.data

    this.setData({
      isRefilling: true,
      answers: buildInitialAnswers(questions),
      answeredCount: 0
    })

    this.setCurrentQuestion(questions, 0)
  },
  goPrev() {
    const { currentQuestionIndex, questions } = this.data

    if (currentQuestionIndex <= 0) {
      return
    }

    const newIndex = currentQuestionIndex - 1

    this.setCurrentQuestion(questions, newIndex)

    wx.pageScrollTo({
      scrollTop: 0,
      duration: 200
    })
  },
  goNext() {
    const { currentQuestionIndex, questions, answers, currentQuestion } = this.data

    if (!currentQuestion) {
      return
    }

    const questionId = currentQuestion.subjectId
    const currentAnswer = answers[questionId]

    if (!hasAnswer(currentAnswer)) {
      wx.showToast({
        title: '请先选择答案',
        icon: 'none'
      })
      return
    }

    if (currentQuestionIndex >= questions.length - 1) {
      return
    }

    const newIndex = currentQuestionIndex + 1

    this.setCurrentQuestion(questions, newIndex)

    wx.pageScrollTo({
      scrollTop: 0,
      duration: 200
    })
  },
  async submitQuestionnaire() {
    if (this.data.submitting) {
      return
    }

    const { recordId, answers, questions, totalQuestions, doctorId, patientId, questionnaireId, diseaseType, visitType } = this.data

    const incompleteQuestion = questions.find((question: QuestionnaireQuestion) => !hasAnswer(answers[question.subjectId]))
    if (incompleteQuestion) {
      wx.showToast({ title: '还有题目未填写', icon: 'none' })
      return
    }

    const answersArray = Object.entries(answers).map(([subjectId, value]) => ({
      subjectId: String(subjectId),
      value: String(value)
    }))

    const payload: Record<string, any> = {
      recordId: String(recordId),
      questionnaireId: String(questionnaireId || ''),
      answers: answersArray,
      diseaseType: String(diseaseType || ''),
      visitType: String(visitType || '')
    }

    const resolvedDoctorId = String(doctorId || '').trim()
    const resolvedPatientId = String(patientId || '').trim() || String(getCurrentUserId() || '')
    if (resolvedDoctorId && resolvedDoctorId !== '0') {
      payload.doctorId = resolvedDoctorId
    }
    if (resolvedPatientId && resolvedPatientId !== '0') {
      payload.patientId = resolvedPatientId
    }

    console.log('[questionnaire-submit] payload =', payload)

    const startTime = Date.now()
    console.log('[scale-submit-time] step=click_start cost=', Date.now() - startTime)

    this.setData({ submitting: true })
    wx.showLoading({ title: '保存中...' })

    console.log('[scale-submit-time] step=build_payload_done cost=', Date.now() - startTime)
    try {
      const requestStartTime = Date.now()
      const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
        wx.request({
          url: 'https://miniprogram.huiliaoyiyuan.com/api/questionnaires/submit',
          method: 'POST',
          header: {
            'Content-Type': 'application/json'
          },
          data: payload,
          timeout: 60000,
          success: resolve,
          fail: reject
        })
      })

      console.log('[scale-submit-time] step=request_start cost=', Date.now() - startTime)
      console.log('[scale-submit-time] request_duration_ms=', Date.now() - requestStartTime)

      if (response.statusCode === 200 && response.data) {
        console.log('[scale-submit-time] step=request_success cost=', Date.now() - startTime)
        const responseData = response.data as any
        if (responseData.success) {
          const analysisStatus = String(responseData.analysisStatus || '').trim()
          const isGenerating = analysisStatus === 'generating'
          this.setData({
            submitted: true,
            questionnaireStatus: 'completed',
            isRefilling: false,
            answeredCount: totalQuestions,
            progressPercent: totalQuestions > 0 ? 100 : 0
          })

          console.log('[scale-submit-time] step=ui_update_done cost=', Date.now() - startTime)
          wx.showToast({
            title: isGenerating ? '保存成功，分析生成中' : '保存成功',
            icon: isGenerating ? 'none' : 'success',
            duration: 1500
          })
          completePointsTask('questionnaire_fill')
          if (isGenerating) {
            console.log('[scale-submit-time] analysis_status = generating, message = 保存成功，AI分析生成中，请稍后在量表记录中查看')
          }
        } else {
          console.log('[scale-submit-time] step=response_failed cost=', Date.now() - startTime, 'error=', responseData.error || responseData.message)
          wx.showToast({ title: '保存失败', icon: 'none' })
        }
      } else {
        console.log('[scale-submit-time] step=http_error cost=', Date.now() - startTime, 'status=', response.statusCode)
        wx.showToast({ title: '保存失败', icon: 'none' })
      }
    } catch (error) {
      console.log('[scale-submit-time] step=request_fail cost=', Date.now() - startTime, 'error=', error)
      wx.showToast({ title: '网络错误', icon: 'none' })
    } finally {
      wx.hideLoading()
      this.setData({ submitting: false })
    }
  }
})
