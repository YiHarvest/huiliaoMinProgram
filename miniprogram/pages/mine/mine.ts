Component({
  data: {
    companyInfo: {
      name: '榕慧科技(杭州)有限公司',
      vision: '致力于成为医疗领域最受信赖的AI数字合伙人平台',
      mission: 'AI赋能医疗专家，打造安全专属的数字合伙人',
      address: '杭州滨江区JWK聚才大厦杭州市滨江区滨康路308号JWK聚才大厦2幢24层2406',
      phone: '057185808606',
      email: '107314666@qq.com'
    },
    development: [
      { title: '人工智能医疗研究院', desc: '筹建规划中，致力于前沿医疗AI技术研发' },
      { title: '全国专家网络', desc: '以顶尖专家为核心，辐射学生团队的"星火计划"' }
    ]
  },
  methods: {
    onCopyAddress() {
      wx.setClipboardData({
        data: this.data.companyInfo.address,
        success: () => {
          wx.showToast({ title: '地址已复制', icon: 'success' })
        }
      })
    },
    onCopyPhone() {
      wx.setClipboardData({
        data: this.data.companyInfo.phone,
        success: () => {
          wx.showToast({ title: '电话已复制', icon: 'success' })
        }
      })
    },
    onCopyEmail() {
      wx.setClipboardData({
        data: this.data.companyInfo.email,
        success: () => {
          wx.showToast({ title: '邮箱已复制', icon: 'success' })
        }
      })
    },
    onCallPhone() {
      wx.makePhoneCall({
        phoneNumber: this.data.companyInfo.phone
      })
    }
  }
})
