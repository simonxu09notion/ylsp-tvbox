# 永乐视频 (ylsp.lv) · TVBOX 在线接口源

把 [ylsp.lv](https://www.ylsp.lv) 的视频（分类 / 列表 / 真实 m3u8 播放地址）解析为标准
**TVBOX / 影视仓 在线接口源（MacCMS JSON）**，并提供了两套托管方案，全部代码都在本仓库、可直接部署到 GitHub。

> ⚠️ **关于 `.github/workflows/` 文件**：GitHub REST API 出于安全工作流注入防护，**禁止通过接口写入 `.github/workflows/` 目录**，因此本仓库目前**未包含** `deploy.yml` / `refresh.yml`（它们只存在于你本地的 `ylsp-github/.github/workflows/`）。
> 补齐方式（任选其一）：
> - **A 方案（Vercel）不受影响**：直接导入本仓库即可，无需 workflow 文件。
> - **B 方案（GitHub Pages 自动部署）需补齐**：在 GitHub 网页「Add file → Create new file」路径填 `.github/workflows/deploy.yml` 粘贴本地该文件内容；或在你**本地有 git 的环境**执行 `git push`（本地仓库已含全部 10 个文件，含 workflow）。

## 两种在线接口（选其一，或都留着切换）

| 方案 | 地址形态 | 能力 | 部署方式 |
|------|----------|------|----------|
| **A. 动态接口（推荐）** | `https://<项目>.vercel.app/` | 完整支持 分类列表 / 详情 / 搜索，播放精准 | Vercel 一键导入本仓库 |
| **B. GitHub Pages 静态（轻量）** | `https://<用户名>.github.io/<仓库>/api.json` | 浏览 + 播放（部分 App 读取列表内播放地址即可）；搜索为全量返回 | 开启 GitHub Pages（Actions 已写好） |

> 为什么需要 A？TVBOX/CatVod 在点击播放时会再请求 `?ac=detail&ids=xxx` 并取返回列表**第一项**。
> 纯静态文件无法按 id 路由，可能导致「只有第一条能正确播放」。动态接口按需返回精准条目，规避该问题。
> 若你的 App 读取列表内 `vod_play_url` 直接播放，则 B 也能用。

## 仓库结构

```
ylsp-github/
├── api/index.py            # A 方案：Vercel Python Serverless 动态接口
├── vercel.json             # Vercel 配置
├── make_api.py             # 把 ylsp_data.json 转为标准 MacCMS JSON
├── build_subscription.py   # 爬虫：抓取 ylsp.lv → ylsp_data.json
├── ylsp_data.json          # 抓取快照（分类/视频/ m3u8）
├── public/api.json         # B 方案：静态接口文件（由 make_api.py 生成）
├── ylsp_online_subscription.json  # TVBOX 订阅源（含两个站点）
├── .github/workflows/
│   ├── deploy.yml          # 部署 B 到 GitHub Pages
│   └── refresh.yml         # 每日重爬并把最新数据提交回仓库（供 A 读取）
└── README.md
```

## 一、部署到 GitHub 并启用

```bash
cd ylsp-github
git init
git add -A
git commit -m "init: 永乐视频 TVBOX 在线接口源"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

### 启用 B（GitHub Pages 静态）
有两种方式：
- **方式 1（推荐，无需 workflow）**：仓库 → **Settings → Pages → Build and deployment → Source 选 "Deploy from a branch" → 选 `main` 分支 + 目录 `/public`**。保存后 `public/api.json` 即发布到 `https://<用户名>.github.io/<仓库>/api.json`（无需 Actions，`deploy.yml` 不是必须）。
- **方式 2（自动化）**：先把上文的 `deploy.yml` 补进 `.github/workflows/`（见顶部说明），再选 **Source = "GitHub Actions"**，推送后自动构建发布。

### 启用 A（Vercel 动态接口，推荐）
1. 打开 https://vercel.com → **Add New → Project** → 导入上面的 GitHub 仓库。
2. Framework 选 **Other**，默认会按 `vercel.json` 把 `api/index.py` 部署为 Serverless。
3. 部署完成后地址即 `https://<项目名>.vercel.app/`。Vercel 已连接 GitHub，后续推送自动更新。
4. `refresh.yml` 每天会把最新爬取数据提交回仓库，Vercel 重新部署即生效。

## 二、在 TVBOX / 影视仓 中使用

打开 `ylsp_online_subscription.json`，把里面的占位地址替换为你的实际地址：

- A 方案：`"api": "https://<你的Vercel项目名>.vercel.app/"`
- B 方案：`"api": "https://<你的GitHub用户名>.github.io/<仓库名>/api.json"`

然后把该 JSON 作为「订阅」导入即可。`type: "json"` 表示在线接口源（非爬虫、非本地包）。

## 三、本地自测

```bash
# 静态接口本地预览
python -m http.server 8777 --directory public
# 浏览器/ curl 访问 http://127.0.0.1:8777/api.json?ac=list&t=2&pg=1

# 动态接口本地预览（模拟 Vercel handler）
python -c "import api.index as m, urllib.parse; print(m.build_response(urllib.parse.parse_qs('ac=detail&ids=<某视频id>')))"
```

## 说明
- 视频流均为 HLS (m3u8)，直连 CDN（vhmzy.com / bfvvs.com）。
- `refresh.yml` 每日（UTC 17:30）重爬刷新；也可手动在 Actions 页点 `Run workflow`。
- 本仓库仅做结构解析与可达性验证，站点与播放地址为公开可访问的第三方聚合源。
