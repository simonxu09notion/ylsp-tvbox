#!/usr/bin/env bash
# 永乐视频 TVBOX 在线接口 —— Vercel 一键部署脚本 (Git Bash / WSL / macOS)
# 用法:
#   1) 先确保已安装 Node.js (含 npx)
#   2) 交互式:   bash deploy.sh
#      非交互:   VERCEL_TOKEN=xxxx bash deploy.sh   (token 在 vercel.com -> Settings -> Tokens 获取)
set -e

# 进入脚本所在目录（仓库根）
cd "$(dirname "$0")"

TOKEN="${VERCEL_TOKEN:-}"

# 尽量先拉取最新（失败也不阻断）
git pull --ff-only 2>/dev/null || true

echo "==> 永乐视频 Vercel 部署"
echo "==> 目录: $(pwd)"

if [ -n "$TOKEN" ]; then
  echo "==> 使用 VERCEL_TOKEN 进行非交互部署"
  npx -y vercel@latest deploy --prod --yes --token "$TOKEN" --name ylsp-tvbox
else
  echo "==> 未检测到 VERCEL_TOKEN，将使用已登录的 Vercel 账号（否则会自动打开浏览器登录）"
  npx -y vercel@latest deploy --prod --yes
fi

echo ""
echo "==> 部署完成。根地址 https://<项目名>.vercel.app/ 经 vercel.json 重写指向 /api 接口"
echo "==> 验证列表: https://<项目名>.vercel.app/?ac=list&t=1&pg=1"
echo "==> 验证详情: https://<项目名>.vercel.app/?ac=detail&ids=1"
