# Claude Code スキル活用 — 勉強会共有メモ

## 作ったスキル一覧

### 1. humanize — AIくささ除去

AI生成文から「AIっぽい表現」を検出・修正するスキル。

- `/humanize ファイルパス` で実行
- NG語彙リスト（「浮き彫りにする」→「分かった」等）でチェック
- 構造パターン（太字の多用等）も検出
- 修正後にセルフ監査パスを実行

[SKILL.md](https://github.com/mikkegt/claude/blob/main/skills/humanize/SKILL.md)

### 2. read-article — 記事を一緒に読む

記事やXスレッドの内容を、自分の現状（CLAUDE.md、Memory、Issue）と照合して仕訳するスキル。

- 「既にやっていること」「新しい情報」「関連するIssue」の3カテゴリに分類
- 一次情報チェック（まとめ記事なら元ソースを提示）
- バズ記事の煽りに乗らず冷静に判定

[SKILL.md](https://github.com/mikkegt/claude/blob/main/skills/read-article/SKILL.md)

### 3. issue-index — Issueキャッシュ

上記スキルを使う中で「毎回gh issue listを叩くのはトークンの無駄」と気づき、ローカルキャッシュの仕組みを作った。

---

## issue-index の詳細

### 課題

- Claude Codeのスキル（read-article等）や朝ブリーフィングが、毎回 `gh issue list` やGraphQL APIを叩いていた
- Issueが増えるほどトークン消費が増える
- 毎回同じデータを取得している

## 解決策

Issue一覧をローカルJSONにキャッシュし、`Read` だけで参照する仕組みを作った。

## 構成

```
公開リポジトリ（汎用）
  skills/issue-index/sync.sh    ← GraphQLでIssue取得→JSON生成
  skills/issue-index/SKILL.md   ← スキル定義（参照ルール）

プライベートリポジトリ（固有）
  .env.issue-index              ← リポジトリ名・プロジェクト番号
  .issue-index.json             ← 生成されたキャッシュ（.gitignore）
  .claude/settings.json         ← SessionStart hookでsync自動実行
```

## ポイント

1. **スキルの自動判断だけでは不十分だった** — CLAUDE.mdに明示的に「.issue-index.jsonを使え」と書かないと、gh issue listを叩きにいった
2. **SessionStart hook** で自動sync。長時間セッションではスキル側で鮮度チェック（24時間超なら再sync）
3. **汎用と固有を分離** — スクリプト本体は公開リポジトリ、プロジェクト固有設定は.envファイル。setup.shで新マシンでもワンコマンドセットアップ

## 画面共有で見せるファイル

- [sync.sh（本体）](https://github.com/mikkegt/claude/blob/main/skills/issue-index/sync.sh)
- [SKILL.md（スキル定義）](https://github.com/mikkegt/claude/blob/main/skills/issue-index/SKILL.md)
- [setup.sh（ワンコマンドセットアップ）](https://github.com/mikkegt/claude/blob/main/setup.sh)

### プロジェクト固有設定の例

`.env.issue-index`:
```sh
OWNER=mikkegt
REPO=mikkegt/Jarvis
PROJECT_NUMBER=7
```

`.claude/settings.json`（SessionStart hook）:
```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash ~/workspace/github.com/mikkegt/claude/skills/issue-index/sync.sh ."
      }]
    }]
  }
}
```

## Before / After

### Before
```
おはよう
  → gh issue list --label "urgent" （API呼び出し）
  → gh issue list --label "soon"   （API呼び出し）
  → gh issue list --label "waiting" （API呼び出し）
  → gh api graphql ...              （期限取得）
```

### After
```
おはよう
  → Read .issue-index.json （ローカルファイル1回読むだけ）
```
