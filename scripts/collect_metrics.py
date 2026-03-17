#!/usr/bin/env python3
"""
CHOIIZUKA Metrics Collector
GitHub Actions で毎日実行。YouTube + X からデータ取得し
data/daily_metrics.csv と ADMIN_STATS.md を更新する。

Required Secrets:
  YT_API_KEY       - YouTube Data API v3 キー
  YT_CHANNEL_ID    - チャンネルID（UC...）
  X_BEARER_TOKEN   - X API Bearer Token
  X_USERNAME       - X ユーザー名（@なし）
"""

import os
import csv
import json
import datetime
import requests
from dateutil import parser as dtparser

# ===== 設定 =====
YT_API_KEY     = os.getenv("YT_API_KEY", "")
YT_CHANNEL_ID  = os.getenv("YT_CHANNEL_ID", "")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
X_USERNAME     = os.getenv("X_USERNAME", "")

OUT_CSV        = "data/daily_metrics.csv"
ADMIN_MD       = "ADMIN_STATS.md"
DAYS_BACK      = 1  # 昨日分のみ取得（1日1回実行前提）

CSV_HEADER = [
    "date", "source", "event_id",
    "start_iso", "end_iso", "duration_h",
    "live_flag", "viewer_peak", "title_or_text"
]

# ===== ユーティリティ =====
def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0)

def yesterday_range():
    now = utc_now()
    start = (now - datetime.timedelta(days=DAYS_BACK)).replace(hour=0, minute=0, second=0)
    end   = now.replace(hour=23, minute=59, second=59)
    return start.isoformat() + "Z", end.isoformat() + "Z"

def calc_duration_h(start_str, end_str):
    try:
        s = dtparser.parse(start_str)
        e = dtparser.parse(end_str)
        return round((e - s).total_seconds() / 3600, 2)
    except Exception:
        return 0.0

# ===== YouTube =====
def fetch_youtube():
    if not YT_API_KEY or not YT_CHANNEL_ID:
        print("[YouTube] credentials missing — skip")
        return []

    since, until = yesterday_range()
    rows = []

    # Step1: 完了済みライブ動画を検索
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "key": YT_API_KEY,
            "channelId": YT_CHANNEL_ID,
            "part": "id,snippet",
            "publishedAfter": since,
            "type": "video",
            "eventType": "completed",
            "maxResults": 50,
        },
        timeout=30,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]

    if not video_ids:
        print("[YouTube] no completed streams found")
        return []

    # Step2: 詳細取得
    resp2 = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "key": YT_API_KEY,
            "id": ",".join(video_ids),
            "part": "snippet,liveStreamingDetails",
        },
        timeout=30,
    )
    resp2.raise_for_status()

    for v in resp2.json().get("items", []):
        live = v.get("liveStreamingDetails", {})
        snip = v.get("snippet", {})
        start = live.get("actualStartTime") or snip.get("publishedAt", "")
        end   = live.get("actualEndTime", "")
        peak  = live.get("concurrentViewers", "")
        title = snip.get("title", "").replace("\n", " ")[:120]
        date  = start[:10] if start else utc_now().date().isoformat()
        dur   = calc_duration_h(start, end) if end else 0.0

        rows.append({
            "date": date,
            "source": "youtube",
            "event_id": v.get("id", ""),
            "start_iso": start,
            "end_iso": end,
            "duration_h": dur,
            "live_flag": 1,
            "viewer_peak": peak,
            "title_or_text": title,
        })

    print(f"[YouTube] fetched {len(rows)} streams")
    return rows

# ===== X (Twitter) =====
def fetch_x():
    if not X_BEARER_TOKEN or not X_USERNAME:
        print("[X] credentials missing — skip")
        return []

    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    rows = []

    # ユーザーID取得
    r = requests.get(
        f"https://api.twitter.com/2/users/by/username/{X_USERNAME}",
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    user_id = r.json()["data"]["id"]

    # ツイート取得（直近100件）
    since, _ = yesterday_range()
    r2 = requests.get(
        f"https://api.twitter.com/2/users/{user_id}/tweets",
        headers=headers,
        params={
            "max_results": 100,
            "tweet.fields": "created_at,public_metrics",
            "start_time": since,
        },
        timeout=30,
    )
    r2.raise_for_status()

    for t in r2.json().get("data", []):
        created = t.get("created_at", "")
        date    = created[:10] if created else utc_now().date().isoformat()
        text    = t.get("text", "").replace("\n", " ")[:120]

        rows.append({
            "date": date,
            "source": "x",
            "event_id": t.get("id", ""),
            "start_iso": created,
            "end_iso": "",
            "duration_h": 0.0,
            "live_flag": 0,
            "viewer_peak": "",
            "title_or_text": text,
        })

    print(f"[X] fetched {len(rows)} posts")
    return rows

# ===== CSV 追記 =====
def append_csv(rows):
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    exists = os.path.exists(OUT_CSV)

    # 既存IDを読み込んで重複排除
    existing_ids = set()
    if exists:
        with open(OUT_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_ids.add(row.get("event_id", ""))

    new_rows = [r for r in rows if r["event_id"] not in existing_ids]
    if not new_rows:
        print("[CSV] no new rows to append")
        return 0

    with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not exists:
            w.writeheader()
        w.writerows(new_rows)

    print(f"[CSV] appended {len(new_rows)} new rows → {OUT_CSV}")
    return len(new_rows)

# ===== ADMIN_STATS.md 生成 =====
def generate_admin_md():
    if not os.path.exists(OUT_CSV):
        md = f"# ADMIN_STATS\n\nNo data yet. Generated: {utc_now().isoformat()}Z\n"
        with open(ADMIN_MD, "w", encoding="utf-8") as f:
            f.write(md)
        return

    rows = []
    with open(OUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    yt_rows  = [r for r in rows if r["source"] == "youtube"]
    x_rows   = [r for r in rows if r["source"] == "x"]

    total_live_h  = sum(float(r["duration_h"] or 0) for r in yt_rows)
    stream_count  = len(yt_rows)
    post_count    = len(x_rows)

    # 日別集計
    by_date = {}
    for r in yt_rows:
        d = r["date"]
        by_date.setdefault(d, {"h": 0.0, "count": 0})
        by_date[d]["h"]     += float(r["duration_h"] or 0)
        by_date[d]["count"] += 1

    avg_h = (total_live_h / len(by_date)) if by_date else 0.0

    md_lines = [
        "# ADMIN_STATS",
        "",
        f"**Auto-generated by GitHub Actions**: {utc_now().isoformat()}Z",
        "",
        "## Summary",
        "",
        f"| 指標 | 値 |",
        f"|------|-----|",
        f"| YouTube配信 累計時間 | {total_live_h:.1f}h |",
        f"| YouTube配信 累計本数 | {stream_count} |",
        f"| 1日平均配信時間 | {avg_h:.1f}h |",
        f"| X投稿数 | {post_count} |",
        f"| データ取得期間 | 直近{DAYS_BACK}日分/回（累積） |",
        "",
        "## Daily Breakdown (YouTube)",
        "",
        "| 日付 | 配信時間(h) | 配信本数 |",
        "|------|------------|---------|",
    ]
    for d in sorted(by_date.keys(), reverse=True)[:14]:
        md_lines.append(f"| {d} | {by_date[d]['h']:.1f} | {by_date[d]['count']} |")

    md_lines += [
        "",
        "---",
        "",
        "*Source: YouTube Data API v3 / X API v2*",
        "*See data/daily_metrics.csv for raw data*",
    ]

    with open(ADMIN_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"[MD] generated {ADMIN_MD}")

# ===== main =====
def main():
    rows = []
    try:
        rows += fetch_youtube()
    except Exception as e:
        print(f"[YouTube] error: {e}")
    try:
        rows += fetch_x()
    except Exception as e:
        print(f"[X] error: {e}")

    append_csv(rows)
    generate_admin_md()
    print("[Done]")

if __name__ == "__main__":
    main()
