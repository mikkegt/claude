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
