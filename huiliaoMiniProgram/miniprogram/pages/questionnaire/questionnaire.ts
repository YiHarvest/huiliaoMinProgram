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
  answerValue?: string
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
    initialAnswers[question.subjectId] = question.answerValue || ''
  })

  return initialAnswers
}

function countAnsweredQuestions(answers: Record<string, string>) {
  return Object.values(answers).filter((value) => value !== '').length
}

function calcProgressPercent(answeredCount: number, totalCount: number) {
  if (!totalCount) {
    return 0
  }

  return Math.round((answeredCount / totalCount) * 100)
}

Page({
  data: {
    recordId: '',
    templateId: '',
    questionnaireName: '',
    description: '',
    questions: [] as QuestionnaireQuestion[],
    answers: {} as Record<string, string>,
    totalCount: 0,
    totalQuestions: 0,
    answeredCount: 0,
    progressPercent: 0,
    loading: true,
    submitted: false,
    questionnaireStatus: '',
    isRefilling: false
  },
  onLoad(options: { recordId?: string }) {
    console.log('questionnaire onLoad options', options)
    console.log('questionnaire onLoad recordId', options && options.recordId)
    console.log('questionnaire current route', getCurrentPages().map(p => p.route))
    if (options && options.recordId) {
      this.setData({
        recordId: options.recordId
      })
      this.loadQuestionnaire()
    }
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
        console.log('detail response', data)
        console.log('detail response questions', data && data.questions)
        
        const responseData = data || {}
        const questionsArray = Array.isArray(responseData.questions) ? responseData.questions : []
        console.log('questionsArray', questionsArray)

        const questions = questionsArray.map((item: any, questionIndex: number) => ({
          subjectId: String(item.id || item.subjectId || ''),
          title: item.title || '',
          type: item.type,
          options: Array.isArray(item.options)
            ? item.options.map((option: any, optionIndex: number) => ({
                value: String(option.value !== undefined && option.value !== null ? option.value : (option.id !== undefined && option.id !== null ? option.id : optionIndex + 1)),
                label: String(option.label !== undefined && option.label !== null ? option.label : (option.title !== undefined && option.title !== null ? option.title : (option.text !== undefined && option.text !== null ? option.text : '')))
              }))
            : []
        }))
        console.log('mapped questions', questions)
        console.log('first question options', questions[0] && questions[0].options)
        // 打印第三题的完整对象
        if (questions.length >= 3) {
          console.log('=== 第三题完整对象 ===')
          console.log('title:', questions[2].title)
          console.log('type:', questions[2].type)
          console.log('options:', questions[2].options)
          console.log('isRequired:', questions[2].isRequired)
          console.log('subjectId:', questions[2].subjectId)
          console.log('=====================')
        }

        const totalQuestions = questions.length
        const submitted = responseData.status === 'completed'
        const initialAnswers = buildInitialAnswers(questions)
        const answeredCount = countAnsweredQuestions(initialAnswers)
        const progressPercent = calcProgressPercent(answeredCount, totalQuestions)
        
        this.setData({
          recordId: String(responseData.recordId || recordId),
          templateId: String(responseData.templateId || ''),
          questionnaireName: responseData.questionnaireName || '',
          description: responseData.description || '',
          questions,
          answers: initialAnswers,
          totalCount: totalQuestions,
          totalQuestions: totalQuestions,
          answeredCount,
          progressPercent,
          loading: false,
          submitted,
          questionnaireStatus: responseData.status || '',
          isRefilling: false
        })
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
    console.log('answer change subjectId', subjectId)
    console.log('answer change value', value)
    
    const nextAnswers = {
      ...this.data.answers,
      [subjectId]: value
    }
    
    const answeredCount = Object.values(nextAnswers).filter(v => String(v).trim() !== '').length
    const totalQuestions = this.data.totalQuestions
    const progressPercent = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0
    
    console.log('answers', nextAnswers)
    console.log('answeredCount', answeredCount, 'totalQuestions', totalQuestions, 'progressPercent', progressPercent)
    
    this.setData({
      answers: nextAnswers,
      answeredCount,
      progressPercent
    })
  },
  handleTextInput(e: WechatMiniprogram.CustomEvent) {
    const subjectId = String(e.currentTarget.dataset.subjectId || '')
    const value = String(e.detail.value || '')
    console.log('text input subjectId', subjectId)
    console.log('text input value', value)
    
    const nextAnswers = {
      ...this.data.answers,
      [subjectId]: value
    }
    
    const answeredCount = Object.values(nextAnswers).filter(v => String(v).trim() !== '').length
    const totalQuestions = this.data.totalQuestions
    const progressPercent = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0
    
    console.log('answers', nextAnswers)
    console.log('answeredCount', answeredCount, 'totalQuestions', totalQuestions, 'progressPercent', progressPercent)
    
    this.setData({
      answers: nextAnswers,
      answeredCount,
      progressPercent
    })
  },
  startRefillQuestionnaire() {
    const answeredCount = countAnsweredQuestions(this.data.answers)
    const totalQuestions = this.data.totalQuestions
    const progressPercent = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0

    this.setData({
      isRefilling: true,
      answeredCount,
      progressPercent
    })
  },
  async submitQuestionnaire() {
    const { recordId, answers, questions, totalQuestions } = this.data

    // 验证必填项
    const requiredQuestions = questions.filter((q: QuestionnaireQuestion) => q.isRequired)
    const missingRequired = requiredQuestions.some((q: QuestionnaireQuestion) => !answers[q.subjectId])
    if (missingRequired) {
      wx.showToast({ title: '请完成所有必填题目', icon: 'none' })
      return
    }
    
    // 构建答案数组
    const answersArray = Object.entries(answers).map(([subjectId, value]) => ({
      subjectId: String(subjectId),
      value: String(value)
    }))
    
    // 调试日志
    console.log('=== 前端提交调试信息 ===')
    console.log('recordId:', recordId)
    console.log('typeof recordId:', typeof recordId)
    console.log('answers:', answers)
    console.log('answersArray:', answersArray)
    console.log('typeof first subjectId:', typeof (answersArray[0] && answersArray[0].subjectId))
    
    const payload = {
      recordId: String(recordId),
      answers: answersArray
    }
    console.log('最终请求体 JSON:', JSON.stringify(payload, null, 2))
    
    wx.showLoading({ title: '提交中...' })
    try {
      const response = await new Promise<WechatMiniprogram.RequestSuccessCallbackResult>((resolve, reject) => {
        wx.request({
          url: 'https://miniprogram.huiliaoyiyuan.com/api/questionnaires/submit',
          method: 'POST',
          data: payload,
          success: resolve,
          fail: reject
        })
      })
      
      if (response.statusCode === 200 && response.data) {
        const responseData = response.data as any
        if (responseData.success) {
          this.setData({
            submitted: true,
            questionnaireStatus: 'completed',
            isRefilling: false,
            answeredCount: totalQuestions,
            progressPercent: totalQuestions > 0 ? 100 : 0
          })

          wx.showToast({ 
            title: '提交成功', 
            icon: 'success',
            duration: 2000
          })
        } else {
          wx.showToast({ title: '提交失败', icon: 'none' })
        }
      } else {
        wx.showToast({ title: '提交失败', icon: 'none' })
      }
    } catch (error) {
      wx.showToast({ title: '网络错误', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  }
})
