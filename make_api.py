#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_api.py
把已爬取的 ylsp_data.json 转换为 TVBOX / 影视仓 标准「在线接口源」所需的
MacCMS JSON 格式, 输出到 public/api.json。

用法:
    python make_api.py            # 直接转换已有 ylsp_data.json
    python make_api.py --refresh  # 先重新爬取 ylsp.lv 刷新数据, 再转换

该文件会被 .github/workflows/deploy.yml 在 GitHub Actions 中调用 (带 --refresh),
实现「每日定时重新爬取 -> 重新生成 api.json -> 部署到 GitHub Pages」的自动刷新。
"""
import json
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_subscription as bc  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
DATA_JSON = os.path.join(ROOT, "ylsp_data.json")
API_JSON = os.path.join(PUBLIC, "api.json")

SITE_NAME = "永乐视频"


def transform(data: dict) -> dict:
    """将抓取快照转换为标准 MacCMS JSON 接口结构。

    TVBOX json 类型源会在列表项里直接读取 vod_play_url 进行播放,
    因此这里把已解析好的 m3u8 直接写入 list 项, 保证静态托管也能直接播放。
    """
    classes = [{"type_id": c["id"], "type_name": c["name"]} for c in data["categories"]]
    name_to_id = {c["name"]: c["id"] for c in data["categories"]}

    lst = []
    for v in data["videos"]:
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
        lst.append(item)

    return {
        "code": 1,
        "msg": "数据列表",
        "page": 1,
        "pagecount": 1,                 # 静态全量返回, 仅 1 页
        "limit": len(lst),
        "total": len(lst),
        "list": lst,
        "class": classes,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="重新爬取 ylsp.lv 刷新数据后再转换")
    args = ap.parse_args()

    if args.refresh:
        try:
            os.environ.setdefault("PER_CAT", "25")
            print("[*] --refresh: 重新爬取 ylsp.lv ...")
            bc.main()
            print("[+] 数据已重新爬取")
        except Exception as e:
            print(f"[!] 重爬失败, 回退使用已有 ylsp_data.json: {e}")

    if not os.path.exists(DATA_JSON):
        sys.exit(f"[X] 找不到 {DATA_JSON}, 请先运行 build_subscription.py 或 --refresh")

    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)

    out = transform(data)

    os.makedirs(PUBLIC, exist_ok=True)
    with open(API_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    with_url = sum(1 for it in out["list"] if it.get("vod_play_url"))
    print(f"[+] 已生成 {API_JSON}")
    print(f"    视频 {out['total']} 条 (含播放地址 {with_url} 条), 分类 {len(out['class'])} 个")


if __name__ == "__main__":
    main()
