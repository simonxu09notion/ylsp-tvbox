@echo off
REM 永乐视频 TVBOX 在线接口 —— Vercel 一键部署脚本 (Windows cmd / PowerShell)
REM 用法:
REM   1) 先确保已安装 Node.js (含 npx) 并重启终端使其生效
REM   2) 交互式:   双击本文件 或 在 cmd 中运行 deploy.bat
REM      非交互:   cmd /C "set VERCEL_TOKEN=xxxx&& deploy.bat"   (token 在 vercel.com -> Settings -> Tokens 获取)
cd /d "%~dp0"

IF "%VERCEL_TOKEN%"=="" (
  echo [INFO] 未检测到 VERCEL_TOKEN，将使用已登录的 Vercel 账号（否则会自动打开浏览器登录）
  npx -y vercel@latest deploy --prod --yes
) ELSE (
  echo [INFO] 使用 VERCEL_TOKEN 进行非交互部署
  npx -y vercel@latest deploy --prod --yes --token %VERCEL_TOKEN% --name ylsp-tvbox
)

echo.
echo [DONE] 部署完成。验证地址形如: https://^<项目名^>.vercel.app/?ac=list^&t=1^&pg=1
pause
