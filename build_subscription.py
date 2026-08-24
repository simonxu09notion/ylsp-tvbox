#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_subscription.py
抓取永乐视频 (https://www.ylsp.lv) 站点结构，提取分类、视频列表及真实 m3u8 播放地址，
生成:
  1) ylsp_data.json                 —— 提取快照(分类/视频列表/播放地址) 供校验与直接查看
  2) ylsp_tvbox_subscription.json   —— TVBOX / 影视仓 兼容订阅源(内嵌 spider base64)
依赖: 仅标准库; 多线程抓取。
"""
import urllib.request, urllib.parse, re, ssl, json, os, base64, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

SITE = "https://www.ylsp.lv"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
CATEGORIES = [("1", "电影"), ("2", "剧集"), ("3", "综艺"), ("4", "动漫")]
PER_CAT = int(os.environ.get("PER_CAT", "25"))   # 每分类提取数量
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, ref=None, timeout=25, binary=False):
    headers = {"User-Agent": UA, "Referer": ref or (SITE + "/")}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "ignore")

def fix_slash(s):
    return s.replace('\\/', '/')

def extract_m3u8(html):
    norm = fix_slash(html)
    m = re.search(r'https?://[^\s"\'\\]+?\.m3u8', norm)
    if not m:
        m = re.search(r'https?://[^\s"\']+?\.m3u8', html)
    return m.group(0) if m else ""

def parse_cards(html):
    out = []
    seen = set()
    for m in re.finditer(
        r'<a href="/voddetail/(\d+)/"[^>]*title="([^"]+)"[\s\S]*?data-original="([^"]*)"[\s\S]*?module-item-note">([^<]*)</div>',
        html):
        vid, title, pic, note = m.group(1), m.group(2), m.group(3), m.group(4)
        if vid in seen:
            continue
        seen.add(vid)
        out.append({
            "id": vid,
            "title": title,
            "pic": pic if pic.startswith("http") else (SITE + pic),
            "remarks": note.strip(),
        })
    return out

def get_play_path_for(vid):
    # 默认第一线路第一集; 若详情页存在则使用真实入口
    return f"/play/{vid}-1-1/"

def worker(vid, title, pic, remarks, cat_name):
    play_path = get_play_path_for(vid)
    try:
        html = fetch(SITE + play_path)
        m3u8 = extract_m3u8(html)
    except Exception as e:
        m3u8 = ""
        html = ""
    return {
        "id": vid,
        "title": title,
        "pic": pic,
        "remarks": remarks,
        "category": cat_name,
        "play_path": play_path,
        "m3u8": m3u8,
    }

def main():
    print(f"[*] 目标站点: {SITE}  (永乐视频)")
    print(f"[*] 每分类提取数量: {PER_CAT}")
    data = {
        "site": SITE,
        "site_name": "永乐视频",
        "spider_class": "ylsp",
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "categories": [{"id": c[0], "name": c[1]} for c in CATEGORIES],
        "videos": [],
    }
    tasks = []
    for cid, cname in CATEGORIES:
        try:
            html = fetch(f"{SITE}/vodtype/{cid}/")
        except Exception as e:
            print(f"[!] 分类 {cname}({cid}) 列表抓取失败: {e}")
            continue
        cards = parse_cards(html)[:PER_CAT]
        print(f"[+] 分类 {cname}({cid}): 解析到 {len(cards)} 个视频条目")
        for c in cards:
            tasks.append((c["id"], c["title"], c["pic"], c["remarks"], cname))

    print(f"[*] 共 {len(tasks)} 个视频待提取播放地址, 多线程抓取中...")
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(worker, *t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results.append(r)
            ok = "OK " if r["m3u8"] else "MISS"
            print(f"    [{i:3d}/{len(tasks)}] {ok} {r['title'][:24]:24s} -> {r['m3u8'][:60]}")
    # 保持分类+原顺序
    results.sort(key=lambda r: (CATEGORIES.index((next(c for c in CATEGORIES if c[1]==r["category"]), ("0",""))[0]), r["id"]))
    data["videos"] = results

    with_ok = sum(1 for r in results if r["m3u8"])
    print(f"[*] 提取完成: {with_ok}/{len(results)} 个视频获得 m3u8 地址")

    # 写出数据快照
    data_path = os.path.join(OUT_DIR, "ylsp_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[+] 已写出数据快照: {data_path}")

    # 写出 TVBOX 订阅源 (内嵌 spider base64)
    spider_path = os.path.join(OUT_DIR, "ylsp_spider.js")
    with open(spider_path, "r", encoding="utf-8") as f:
        spider_js = f.read()
    spider_b64 = base64.b64encode(spider_js.encode("utf-8")).decode("ascii")

    sub = {
        "spider": spider_b64,
        "sites": [
            {
                "key": "ylsp",
                "name": "永乐视频",
                "type": 3,
                "api": "csp_ylsp",
                "searchable": 1,
                "quickSearch": 1,
                "filterable": 0,
                "ext": ""
            }
        ],
        "parges": [],
        "lives": []
    }
    sub_path = os.path.join(OUT_DIR, "ylsp_tvbox_subscription.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(sub, f, ensure_ascii=False, indent=2)
    print(f"[+] 已写出 TVBOX 订阅源: {sub_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        os.environ["PER_CAT"] = sys.argv[1]
    main()
