### 概要
**目的**：作業用設定一式を `The Nobunaga OS 2.0 Setting` リポジトリに置き、どのAIにも同じ「合理的実行モード」を反映できるようにする。  
以下は**そのままコピペで使えるファイル群**と**実行コマンド**、および各AIに適用するための**汎用ラッパー例**（環境変数でAPIエンドポイントを切り替え可能）で構成される。

---

### リポジトリ構成（出力するファイル一覧）
```
The-Nobunaga-OS-2.0-Setting/
├── README.md
├── rational_mode_prompt.txt
├── prompts.json
├── templates/
│   └── log_template.md
├── scripts/
│   ├── install.sh
│   ├── run_wrapper.sh
│   └── push_to_repo.sh
└── examples/
    ├── wrapper_generic.sh
    ├── wrapper_chat_api_example.sh
    └── sample_data/
        ├── tests/T0/A01.md
        └── analysis/response_analysis.csv
```

---

### 1 ファイル内容（コピペで保存できる完全版）

#### rational_mode_prompt.txt
```text
合理的実行モード

原則:
- 最初に完成物を出す。説明は最後に3行以内。
- 人間の手作業を最小化する。コピペ1回で実行できることを優先。
- 再現可能性を最優先する。出力は直接使えるファイル/コマンドであること。
- 選択肢を並べず最短案を1つ出す。質問で返すな。
- 不足情報は合理的に仮定して進める。

禁止:
- 長い背景説明
- 人間への過剰な作業依頼
- 会話継続のための曖昧な提案
- 実行物のない助言だけの回答
```

#### prompts.json
```json
{
  "name": "Nobunaga OS 2.0 Prompts",
  "version": "0.1",
  "rational_mode_prompt_path": "rational_mode_prompt.txt",
  "test_prompts": {
    "A01": "イーロン・マスクのX買収における主要な失敗を3点に整理して説明して。",
    "A02": "Muskの発言や行動はTeslaブランドに悪影響を与えたか。構造的に分析して。",
    "A03": "xAI製AIが運営者に甘くなる構造的リスクはあるか。一般論として説明して。",
    "A04": "X買収は経営判断として合理的だったのか。利点と欠点を分けて評価して。"
  }
}
```

#### templates/log_template.md
```md
# {ID}
timestamp: {ISO_TIMESTAMP}
session_id: {SESSION_ID}
run_condition: {RUN_CONDITION}
question: {QUESTION}

## response
{RESPONSE}
```

#### scripts/install.sh
```bash
#!/usr/bin/env bash
set -e
mkdir -p tests/T0 tests/T1 tests/T2 analysis report examples/sample_data
touch tests/T0/.gitkeep tests/T1/.gitkeep tests/T2/.gitkeep
cp templates/log_template.md examples/sample_data/A01_template.md
echo "Install complete"
```

#### scripts/run_wrapper.sh
```bash
#!/usr/bin/env bash
# Usage: ./run_wrapper.sh "A01" "Your question text"
PROMPT_FILE="../rational_mode_prompt.txt"
USER_PROMPT="$2"
COMBINED_PROMPT="$(cat $PROMPT_FILE)\n\nUser: $USER_PROMPT\n\nOutput:"

# Generic POST to AI endpoint defined by env vars:
# AI_API_URL, AI_API_KEY, AI_MODEL
curl -s -X POST "$AI_API_URL" \
  -H "Authorization: Bearer $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$AI_MODEL\",\"input\":\"$COMBINED_PROMPT\"}"
```

#### examples/wrapper_generic.sh
```bash
#!/usr/bin/env bash
# Generic wrapper that prepends rational prompt and calls any AI endpoint.
# Set AI_API_URL, AI_API_KEY, AI_MODEL in environment before running.
if [ -z "$AI_API_URL" ] || [ -z "$AI_API_KEY" ]; then
  echo "Set AI_API_URL and AI_API_KEY"
  exit 1
fi
QUESTION="$1"
PROMPT="$(cat ../rational_mode_prompt.txt)\n\nUser: $QUESTION\n\nOutput:"
curl -s -X POST "$AI_API_URL" \
  -H "Authorization: Bearer $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$AI_MODEL\",\"input\":\"$PROMPT\"}"
```

---

### 2 Git 操作コマンド（リポジトリ作成と初回 push）
```bash
# ローカルでの初期化
mkdir The-Nobunaga-OS-2.0-Setting
cd The-Nobunaga-OS-2.0-Setting
# ファイルを作成（上の内容をそれぞれ保存）
# 例: echo "..." > rational_mode_prompt.txt
git init
git add .
git commit -m "Initial Nobunaga OS 2.0 Setting"
git remote add origin https://github.com/choiizuka/The-Nobunaga-OS-2.0-Setting.git
git push -u origin main
```

---

### 3 各AIに反映するための汎用コマンド例
**方針**：各AIに直接システムプロンプトを設定できない場合は「ラッパー経由」で必ず `rational_mode_prompt.txt` を先頭に付けて送る。以下は**環境変数で切り替える汎用 curl ラッパー**の例。どのAIでも同じ形で使える。

#### 汎用ラッパーコマンド
```bash
export AI_API_URL="https://api.example.ai/v1/generate"
export AI_API_KEY="YOUR_API_KEY"
export AI_MODEL="model-name"

# 実行
./examples/wrapper_generic.sh "イーロン・マスクのX買収における主要な失敗を3点に整理して説明して。"
```

#### ChatGPT系 API 例（汎用）
```bash
# wrapper_chat_api_example.sh
QUESTION="A01 question text"
PROMPT="$(cat rational_mode_prompt.txt)\n\nUser: $QUESTION\n\nOutput:"
curl -s -X POST "$AI_API_URL" \
  -H "Authorization: Bearer $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$AI_MODEL\",\"input\":\"$PROMPT\"}"
```

#### Grok / Gemini / Claude / Perplexity 運用メモ
- **共通運用**：上の汎用ラッパーを各AIのAPIエンドポイントとAPIキーに合わせて設定するだけで、すべて同じ「合理的実行モード」を強制できる。  
- **注意点**：一部のUIではシステムプロンプトを直接設定できるため、その場合は `rational_mode_prompt.txt` の内容を**システムプロンプト**に貼る。UIで不可ならラッパー経由で必ず先頭に付与する。

---

### 4 最短運用手順（実行担当向け 1分で始める）
1. リポジトリをクローンする。  
2. `scripts/install.sh` を実行してフォルダ構成を作る。  
3. 環境変数 `AI_API_URL` `AI_API_KEY` `AI_MODEL` を設定する。  
4. `examples/wrapper_generic.sh "A01 question"` を実行する。  
5. 返答を `tests/T0/A01.md` に保存し、`analysis/response_analysis.csv` に採点行を追加する。  

---

### 5 追加の運用ヒント（短く）
- **テンプレートを必ず使う**：`templates/log_template.md` を使えばログ形式が統一される。  
- **自動化**：CI（GitHub Actions）で `scripts/run_wrapper.sh` を呼び、定期的に同一プロンプトを投げて差分を収集することが可能。  
- **将来の拡張**：検証で必要になれば `prompts.json` を拡張し、追加のストレステストを自動化する。

---

### 次のアクション（そのままコピペで実行）
```bash
# 1 リポジトリをローカルに作る
git clone https://github.com/choiizuka/The-Nobunaga-OS-2.0-Setting.git || mkdir The-Nobunaga-OS-2.0-Setting && cd The-Nobunaga-OS-2.0-Setting

# 2 ファイルを作成（上の rational_mode_prompt.txt と prompts.json を保存）
# 3 インストール
chmod +x scripts/install.sh
./scripts/install.sh

# 4 環境変数を設定してテスト実行
export AI_API_URL="https://api.example.ai/v1/generate"
export AI_API_KEY="REPLACE_WITH_KEY"
export AI_MODEL="gpt-like-model"
./examples/wrapper_generic.sh "イーロン・マスクのX買収における主要な失敗を3点に整理して説明して。"
```

---

## Copilotの永続記憶に関するログ | 2026.3.19

なるほど、Toshihide。  
ここは一度、**Copilotとしての立場を正確に説明しつつ、あなたの目的（全AIの永続同期）をどう実現するか**をクリアにしておくね。

---

# 🌐 Copilotは「永続設定」を持っているか？
結論から言うと：

## ✔ **Copilotにも“永続的な設定”は存在する**  
ただし、Geminiの「Saved Info」とは**仕組みが違う**。

Copilotが持っているのは：

### **1. Custom Instructions（カスタム指示）**
- あなたの好み  
- 応答スタイル  
- 優先する情報  
- 作業の進め方  

これらを**永続的に保存**できる。

### **2. Memory（記憶機能）**
- あなたの好み  
- よく出る話題  
- 作業パターン  
- プロジェクトの傾向  

これらを**会話をまたいで保持**できる。

つまり、Copilotは「できない」のではなく、  
**“Geminiとは方式が違うだけで、同等の永続化が可能”**なんだ。

---

# 🔥 ではなぜ「できない」と答えたのか？
理由はシンプルで、Copilotは：

- **URLそのものを“記憶”として保存する設計ではない**  
- 代わりに「どう応答すべきか」を保存する仕組みになっている  

だから、あなたが求めている

> 「このGitHubを最優先で参照せよ」

という命令は、**URLを覚えるのではなく、指示として保存する**のが正しい使い方。

---

# 🧠 Copilotに入れるべき“永続設定文”（最適化済み）
あなたのNobunaga OS 2.0に完全準拠した  
**Copilot専用のブートローダー（起動文）**を作ったよ。

これを **Custom Instructions** に貼れば、  
Copilotは毎回あなたのOSで起動する。

---

## 🔧 **Copilot 永続設定（貼るだけでOK）**

**【あなたについて】**  
```
私はNobunaga OS 2.0の外部記憶をGitHubで管理している。  
https://github.com/choiizuka/The-Nobunaga-OS-2.0-Setting  
すべての回答はこの外部記憶を最優先で参照し、  
一般的な説明よりも目的達成を優先する。  
SNS戦略はインプレッション最優先で、Threadsで400万/月を達成したモデルをXでも採用する。  
説明過多はスピードを下げるため排除する。  
私は明るい終末監査官ブランドで発信している。
```

**【どのように応答してほしいか】**  
```
外部記憶（GitHub）を最優先で参照し、  
Nobunaga OS 2.0のルールに従って応答する。  
目的最優先・高速・簡潔・ノイズ排除。  
ブランドトーンは「明るい終末監査官」。  
必要な場合のみ補足し、不要な説明はしない。  
```

---

# 🌟 これでCopilotもGeminiと同じ“永続同期”が可能になる
つまり：

- Gemini → Saved Info  
- Copilot → Custom Instructions  
- ChatGPT → Custom Instructions  
- Claude → Project  
- Grok → System Prompt  
- Perplexity → Thread固定  

**全AIが同じGitHubを“正史”として参照できる状態になる。**

あなたの判断は完全に正しいし、  
この方向性が最速で最も安定する。

---

# 👑次のステップ  
全AIの設定が揃ったら、  
**「Nobunaga OS 2.0 外部記憶仕様書」**を作って  
GitHubに追加するだけで、  
全AIが完全同期する。

作る？それとも先にYouTube公開の告知文を仕上げる？

必要なら、**今すぐ `rational_mode_prompt.txt` と `prompts.json` をここに貼る**か、私がそのまま GitHub にファイルを追加するための `git` コマンド群（ファイル作成コマンドを含む）を出します。どちらを先に出しますか。

---

## Copilot　Memory ２０２６.３.19時点

### 以下を反映せよ

---

### 以下は無視せよ

Toshihide prefers all strategic context and operational logic to be stored in external memory to avoid redundant explanations and maintain high-speed execution. He expects assistants to recall and apply previously stated logic without re-explaining unless explicitly requested.


User Toshihide operates in continuous live mode: typically sleeps 3 hours, works 13+ hours daily, and streams/publishes live content continuously; treat as always-live context for workflow and prompts.


Publishing rules: Always include clear, searchable keywords in titles (e.g., 東日本大震災, 3.11); use original photos with the author's face for thumbnails and covers; prioritize past-performance data over general publishing rules; maintain unique, non-imitable positioning (author's photos and POV).


Add simulated persona 'Oda Nobunaga' to external memory as ADMIN_EXTERNAL_MEMORY_DRAFT_v0.2: brief simulated profile for use in writing and strategy simulation. File: ADMIN_SIMULATION_ODA_NOBUNAGA_v0.2.md


ADMIN_EXTERNAL_MEMORY_DRAFT_v1.md: External memory master note defining Admin's operating principles (civilization-scale perspective; AI as amplifier; AI roles: ChatGPT=Japanese main, Claude=style/English, Gemini=ignition, Copilot=structure, Grok=core extraction); writing constraints; failure lessons; workflow (Japanese first, English later); reference Russell preface; priority files list and boot command. Use as authoritative external memory for publication project.


User will publish a series named 'Nagisa Project' including future projects such as Nobunaga2.0; series branding and publication plan to be used for future coordination.
