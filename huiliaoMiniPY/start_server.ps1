# PowerShell 脚本启动服务器
Write-Host "正在启动聊天服务器..."

# 切换到项目目录
Set-Location "d:\huiliao\huiliao\huiliaoMiniPY"

# 启动服务器
python chat_proxy_server.py
