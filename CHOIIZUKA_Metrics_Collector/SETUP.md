# CHOIIZUKA Metrics Collector — Setup

## 配置するファイル

```
.github/workflows/collect_metrics.yml   ← Actions ワークフロー
scripts/collect_metrics.py              ← 収集スクリプト
data/.gitkeep                           ← dataフォルダ（CSV出力先）
```

## GitHub Secrets の設定

リポジトリ → Settings → Secrets and variables → Actions → New repository secret

| Secret名 | 内容 |
|----------|------|
| `YT_API_KEY` | YouTube Data API v3 キー |
| `YT_CHANNEL_ID` | チャンネルID（`UC`で始まる文字列） |
| `X_BEARER_TOKEN` | X API Bearer Token |
| `X_USERNAME` | Xユーザー名（@なし） |

## 実行タイミング

- **自動**: 毎日 JST 09:00（UTC 00:00）
- **手動**: Actions タブ → `CHOIIZUKA-Metrics-Collector` → Run workflow

## 出力ファイル

| ファイル | 内容 |
|----------|------|
| `data/daily_metrics.csv` | 生データ（YouTube配信 + X投稿） |
| `ADMIN_STATS.md` | 集計サマリー（AI読み込み用） |

## チャンネルIDの確認方法

YouTube Studio → 設定 → チャンネル → 詳細設定 → チャンネルID

## 注意

- X API は無料枠（Basic）でも動作するが取得件数に制限あり
- API キーは絶対にコードに直書きしない → Secrets のみ
- public repo の場合、`data/daily_metrics.csv` に個人情報を含めない
