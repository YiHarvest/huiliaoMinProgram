const faqData = [
  {
    question: '什么是舌诊分析？',
    answer: '舌诊是中医诊断的重要方法之一，通过观察舌头的颜色、形态、舌苔等特征来判断身体的健康状况。我们的AI舌诊系统利用计算机视觉技术，对上传的舌面视频进行分析，为您提供中医体质评估和健康建议。',
    expanded: false
  },
  {
    question: '如何进行舌诊视频录制？',
    answer: '1. 确保在自然光线下拍摄，避免使用闪光灯；\n2. 张开嘴巴，自然伸出舌头；\n3. 保持面部稳定，确保舌头清晰可见；\n4. 录制时间建议在11-19秒之间；\n5. 录制完成后系统会自动进行分析。',
    expanded: false
  },
  {
    question: '为什么录制的视频无法分析？',
    answer: '可能的原因包括：\n1. 视频质量不佳，舌头不清晰；\n2. 录制时长过短或过长；\n3. 光线不足或过曝；\n4. 建议重新录制或从相册选择视频进行分析。',
    expanded: false
  },
  {
    question: '分析报告多久可以生成？',
    answer: '视频上传后，系统会在几秒钟内完成分析并生成报告。如果网络状况不佳，可能需要稍长的时间。',
    expanded: false
  },
  {
    question: '我的数据安全吗？',
    answer: '我们非常重视用户数据的安全和隐私保护。所有上传的视频完成分析后都会删除，生成的报告都经过加密处理，仅用于分析目的，不会泄露给第三方。',
    expanded: false
  },
  {
    question: '分析结果可以作为诊断依据吗？',
    answer: '本系统提供的分析结果仅供参考，不能替代专业医生的诊断。如果您有健康方面的疑虑，请咨询专业的中医师或医生。',
    expanded: false
  },
  {
    question: '如何获取更准确的分析结果？',
    answer: '1. 在光线充足的环境下录制；\n2. 确保舌头完全伸出，清晰可见；\n3. 避免食用有色食物或饮料后立即录制；\n4. 放松身体，自然伸舌，不要用力。',
    expanded: false
  },
  {
    question: '支持哪些设备使用？',
    answer: '本小程序支持微信平台上的iOS和Android设备。建议使用手机摄像头进行视频录制，以获得最佳效果。',
    expanded: false
  },
  {
    question: '如何联系客服？',
    answer: '您可以在"我的"页面点击"联系我们"，获取客服联系方式，包括电话、邮箱等。我们的客服团队会在工作日及时回复您的问题。',
    expanded: false
  },
  {
    question: '是否需要付费使用？',
    answer: '本小程序目前提供免费的舌诊分析服务。后续可能会推出更多增值服务，具体收费标准会提前告知用户。',
    expanded: false
  }
]

Page({
  data: {
    faqList: faqData
  },

  toggleFaq(event: WechatMiniprogram.CustomEvent) {
    const index = event.currentTarget.dataset.index as number
    const faqList = this.data.faqList.map((item, i) => ({
      ...item,
      expanded: i === index ? !item.expanded : false
    }))
    this.setData({ faqList })
  }
})
