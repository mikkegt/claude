# claude

Claude Code のグローバル設定とプロジェクト別テンプレートを管理するリポジトリ。

## セットアップ

### グローバル CLAUDE.md

```bash
ln -s /path/to/this/repo/CLAUDE.md ~/.claude/CLAUDE.md
```

シンボリックリンクを貼ることで、このリポジトリの CLAUDE.md がすべての Claude Code セッションで読み込まれる。

### プロジェクト別テンプレート

```bash
ln -s /path/to/this/repo/templates/python.md /path/to/project/CLAUDE.md
```

プロジェクトの CLAUDE.md にテンプレートへのシンボリックリンクを貼る。プロジェクト固有のルールが必要な場合は、シンボリックリンクではなく実ファイルとして作成する。

## ファイル構成

```
CLAUDE.md       - グローバル設定（英語）
CLAUDE.ja.md    - グローバル設定（日本語訳・参照用）
templates/      - プロジェクト別テンプレート（今後追加）
```

## 読み込み順序

1. `~/.claude/CLAUDE.md`（グローバル）
2. プロジェクトの `CLAUDE.md`（プロジェクト固有）

両方読み込まれるため、プロジェクト側でグローバルの設定を上書きできる。

## 注意事項

- Git操作のルールは GitHub / GitLab 両対応（PR/MR 表記）
- グローバルでは「フィーチャーブランチを切る」がデフォルト。個人プロジェクトでは CLAUDE.md で緩和可能
