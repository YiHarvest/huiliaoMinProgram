const QR_CODE_SRC = '/assets/contact-qrcode.png'

const companyInfo = {
  name: '银川慧疗互联网医院',
  phone: '057185808606',
  email: '107314666@qq.com',
  address: '杭州市滨江区滨康路 308 号 IWK 聚才大厦 2 幢 24 层 2406',
  latitude: 30.2089,
  longitude: 120.2089
}

const contactCards = [
  {
    key: 'address',
    theme: 'address',
    icon: '📍',
    label: '公司地址',
    value: companyInfo.address,
    hint: '',
    action: 'address',
    actionText: '导航',
    toastLabel: '地址'
  },
  {
    key: 'phone',
    theme: 'phone',
    icon: '📞',
    label: '联系电话',
    value: companyInfo.phone,
    hint: '',
    action: 'call',
    actionText: '拨打',
    toastLabel: '电话'
  },
  {
    key: 'email',
    theme: 'email',
    icon: '📧',
    label: '电子邮箱',
    value: companyInfo.email,
    hint: '',
    action: 'copy',
    actionText: '复制',
    toastLabel: '邮箱'
  }
]

Component({
  data: {
    companyInfo,
    contactCards,
    qrcodeSrc: QR_CODE_SRC,
    serviceTags: ['产品咨询', '合作沟通', '专家网络', '公众号']
  },
  methods: {
    onContactAction(event: WechatMiniprogram.CustomEvent) {
      const { action, value, label } = event.currentTarget.dataset as {
        action: 'copy' | 'call' | 'address'
        value: string
        label: string
      }

      if (action === 'call') {
        wx.makePhoneCall({
          phoneNumber: value
        })
        return
      }

      if (action === 'address') {
        wx.showActionSheet({
          itemList: ['复制地址', '打开地图导航'],
          success: (res) => {
            if (res.tapIndex === 0) {
              wx.setClipboardData({
                data: value,
                success: () => {
                  wx.showToast({
                    title: '地址已复制到剪贴板',
                    icon: 'success'
                  })
                }
              })
            } else if (res.tapIndex === 1) {
              wx.openLocation({
                latitude: companyInfo.latitude,
                longitude: companyInfo.longitude,
                name: companyInfo.name,
                address: companyInfo.address,
                scale: 18
              })
            }
          }
        })
        return
      }

      wx.setClipboardData({
        data: value,
        success: () => {
          wx.showToast({
            title: `${label}已复制到剪贴板`,
            icon: 'success'
          })
        }
      })
    },
    onPreviewQrCode() {
      wx.previewImage({
        current: this.data.qrcodeSrc,
        urls: [this.data.qrcodeSrc]
      })
    },
    onServiceTagTap(event: WechatMiniprogram.CustomEvent) {
      const tag = event.currentTarget.dataset.tag as string
      const scrollToMap: Record<string, string> = {
        '产品咨询': 'phone',
        '合作沟通': 'email',
        '专家网络': 'phone',
        '公众号': 'qrcode'
      }
      
      const target = scrollToMap[tag]
      if (target === 'qrcode') {
        wx.pageScrollTo({
          selector: '.follow-card',
          duration: 300
        })
      } else {
        wx.pageScrollTo({
          selector: '.contact-card',
          duration: 300
        })
      }
    }
  }
})
