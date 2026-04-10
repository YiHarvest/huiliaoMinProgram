# 设置Git HOME环境变量
[Environment]::SetEnvironmentVariable("HOME", "D:\CONDA\Git", "User")
[Environment]::SetEnvironmentVariable("HOMEPATH", "D:\CONDA\Git", "User")

# 显示当前环境变量
Write-Host "HOME: $env:HOME"
Write-Host "HOMEPATH: $env:HOMEPATH"

# 验证设置
Write-Host "Git config --list:" -ForegroundColor Green
& "C:\Program Files\Git\bin\git.exe" config --list
