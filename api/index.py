# -*- coding: utf-8 -*-
"""
api/index.py  —— Vercel Python Serverless (TVBOX 在线接口源 / MacCMS JSON API)

TVBOX / 影视仓 的 json 类型源在播放时会请求 ?ac=detail&ids=xxx 并取返回列表第一项,
纯静态文件无法按 id 路由, 因此这里用 Serverless 动态生成响应, 完整支持:
    ?ac=list&t=<分类id>&pg=<页码>     -> 分类列表(分页)
    ?ac=detail&ids=<视频id>           -> 单条详情(含播放地址)
    ?ac=list&wd=<关键词>              -> 搜索
数据来自仓库内的 ylsp_data.json (由 GitHub Actions 每日重新爬取并 commit 刷新)。

部署: 在 Vercel 导入本 GitHub 仓库即可, 默认路由 / 即接口地址。
"""
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "ylsp_data.json")
SITE_NAME = "永乐视频"


def load_data():
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"categories": [], "videos": []}


def build_class(data):
    return [{"type_id": c["id"], "type_name": c["name"]} for c in data.get("categories", [])]


def build_items(data):
    name_to_id = {c["name"]: c["id"] for c in data.get("categories", [])}
    out = []
    for v in data.get("videos", []):
        cid = name_to_id.get(v.get("category", ""), "0")
        item = {
            "vod_id": v["id"],
            "vod_name": v["title"],
            "vod_pic": v.get("pic", ""),
            "type_id": cid,
            "type_name": v.get("category", ""),
            "vod_remarks": v.get("remarks", ""),
        }
        m3u8 = v.get("m3u8", "")
        if m3u8:
            item["vod_play_from"] = SITE_NAME
            item["vod_play_url"] = f"{SITE_NAME}${m3u8}"
        out.append(item)
    return out


def build_response(q):
    data = load_data()
    classes = build_class(data)
    items = build_items(data)
    ac = (q.get("ac", ["list"])[0]).lower()
    t = q.get("t", [""])[0]
    pg = int(q.get("pg", ["1"])[0] or 1)
    limit = int(q.get("limit", ["20"])[0] or 20)
    wd = q.get("wd", [""])[0].strip().lower()
    ids = [x for x in q.get("ids", [""])[0].split(",") if x]

    # 搜索
    if wd:
        matched = [it for it in items if wd in it["vod_name"].lower()]
        return {
            "code": 1, "msg": "搜索结果", "page": 1,
            "pagecount": 1, "limit": len(matched), "total": len(matched),
            "list": matched, "class": classes,
        }

    # 详情: 只返回命中的视频(含播放地址), 取第一项的是 TVBOX 解析器, 必须精准
    if ac == "detail" and ids:
        hit = [it for it in items if it["vod_id"] in ids]
        return {
            "code": 1, "msg": "ok", "page": 1,
            "pagecount": 1, "limit": len(hit), "total": len(hit),
            "list": hit, "class": classes,
        }

    # 列表: 支持分类过滤 + 分页
    if t:
        items = [it for it in items if it["type_id"] == t]
    total = len(items)
    pagecount = max(1, (total + limit - 1) // limit) if limit else 1
    start = (pg - 1) * limit
    page_items = items[start:start + limit]
    return {
        "code": 1, "msg": "数据列表", "page": pg,
        "pagecount": pagecount, "limit": limit, "total": total,
        "list": page_items, "class": classes,
    }


class handler(BaseHTTPRequestHandler):
    def _send(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        try:
            self._send(build_response(q))
        except Exception as e:
            self._send({"code": 0, "msg": f"error: {e}", "list": [], "class": []})

    def log_message(self, *args):
        pass
