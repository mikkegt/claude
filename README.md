# claude

Claude Code のグローバル設定、ルール、Skillを管理するリポジトリ。

## ファイル構成

```
CLAUDE.md       - グローバル設定（~/.claude/CLAUDE.md にシンボリックリンク）
rules/          - 開発ルール（コーディングファイルに触れた時に注入される）
  git.md        - Git操作ルール
  coding.md     - コーディングスタイル・デバッグ・テスト
  workflow.md   - バグ修正/機能要望ワークフロー・ドキュメントメンテ
settings.json   - グローバル設定のバックアップ（手動コピー用）
skills/         - 汎用Skill
setup.sh        - プロジェクト別セットアップスクリプト
```

## グローバルセットアップ

```bash
# CLAUDE.md
ln -s /path/to/this/repo/CLAUDE.md ~/.claude/CLAUDE.md

# rules/ （グローバルに効かせる場合）
ln -s /path/to/this/repo/rules ~/.claude/rules
```

## プロジェクト別セットアップ

```bash
cd /path/to/your/project

# 個人プロジェクト: rules/ をシンボリックリンク
/path/to/this/repo/setup.sh personal

# チームプロジェクト: CLAUDE.local.md + rules/ をコピー、.gitignore に追記
/path/to/this/repo/setup.sh team
```

## Skills 一覧

| スキル | 用途 |
|--------|------|
| `humanize` | 生成文章を人間っぽい表現に直す |
| `issue-index` | Issue一覧をローカルキャッシュしてトークン節約 |
| `note-audio` | 学習ノートを物語調ナレーションに整形し Gemini TTS (Kore) で音声化 |
| `read-article` | 記事を読んで現状と照合し「新しい情報 / 既にやっている / 関連Issue」に仕訳 |
| `review-pr` | Pull Requestを5軸でレビュー |
| `transcript-analyzer` | Claude Codeのセッションログを集計しツール/スキル失敗率を出す |

## Skills の配布方法

### シンボリックリンクで配布する

このリポジトリの `skills/` にオリジナルを管理し、各プロジェクトからシンボリックリンクを貼る。

```bash
# シンボリックリンク作成
ln -s /path/to/this/repo/skills/humanize /path/to/project/.claude/skills/humanize

# .git/info/exclude に追記（プロジェクト側）
echo '.claude/skills/humanize/' >> /path/to/project/.git/info/exclude
```

**注意:** シンボリックリンクを貼った直後にスキル一覧に反映されないことがある（2026-04 確認）。見えない場合は少し時間をおくか、新しいセッションで試す。

### `.git/info/exclude` とは

`.gitignore` と同じ書式で、ローカル限定の git 除外設定。`.gitignore` と違ってリポジトリにコミットされないので、個人用ファイルの除外に使える。

- 場所: `<プロジェクト>/.git/info/exclude`
- 書式: `.gitignore` と同じ（パターン 1 行 1 件）
- 用途: 個人用スキル、ローカル設定ファイル、テストデータなど

## Hooks が必要なスキル

以下のスキルはセッション開始時のhookが必要。`setup.sh` が `.env.issue-index` を検出すれば自動設定する。

| スキル | hook | 条件 |
|--------|------|------|
| issue-index | セッション開始時にsync.sh実行 | `.env.issue-index` がプロジェクトルートにある |

手動設定する場合は `.claude/settings.json` に以下を追加:

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash /path/to/claude/skills/issue-index/sync.sh ."
      }]
    }]
  }
}
```

## 設計思想

- **CLAUDE.md** にはセッション開始時に必要な情報だけ置く（ユーザー情報、行動原則）
- **rules/** には開発中に効くルールを置く（該当ファイルに触れた時に注入される）
- プロジェクト固有のルールは各リポジトリの `.claude/rules/` に直接追加する

## 読み込み順序

1. `~/.claude/CLAUDE.md`（グローバル）
2. `~/.claude/rules/`（グローバルルール）
3. プロジェクトの `CLAUDE.md`（プロジェクト固有）
4. プロジェクトの `.claude/rules/`（プロジェクト固有ルール）

rules/ は該当パスのファイルに触れた時点で注入される。CLAUDE.md よりセッション後半で効きやすい。
